import os
import random

import math
from binascii import hexlify
from time import perf_counter

import itertools
from typing import Union

import pytest
from ledger.stores.binary_file_store import BinaryFileStore

from ledger.stores.chunked_file_store import ChunkedFileStore
from ledger.stores.text_file_store import TextFileStore


def getValue(key, need_binary=False) -> Union[str, bytes]:
    val = str(key).encode() + b'\xe2\x1fC\x89f\xc3\xa1T\xb8\x9b'
    if not need_binary:
        val = hexlify(val).decode()
    return val


chunkSize = 3
dataSize = 101


def data(need_binary=False):
    return [getValue(i, need_binary=need_binary) for i in range(1, dataSize + 1)]


@pytest.fixture(scope="module", params=[TextFileStore, BinaryFileStore])
def chunkedTextFileStore(request) -> ChunkedFileStore:
    return ChunkedFileStore("/tmp", "chunked_data", True, True, chunkSize,
                            chunkStoreConstructor=request.param)


@pytest.yield_fixture(scope="module")
def populatedChunkedFileStore(chunkedTextFileStore) -> ChunkedFileStore:
    store = chunkedTextFileStore
    store.reset()
    dirPath = "/tmp/chunked_data"
    entries = data(need_binary=isinstance(store.currentChunk, BinaryFileStore))
    for d in entries:
        store.put(d)
    assert len(os.listdir(dirPath)) == math.ceil(dataSize / chunkSize)
    assert all(sum(1 for _ in store._openChunk(chunk)._lines()) <= chunkSize
               for chunk in store._listChunks())
    yield store
    store.close()


def testWriteToNewFileOnceChunkSizeIsReached(populatedChunkedFileStore):
    pass


def testRandomRetrievalFromChunkedFiles(populatedChunkedFileStore):
    keys = [2*chunkSize,
            3*chunkSize+1,
            3*chunkSize+chunkSize,
            random.randrange(1, dataSize + 1)]
    store = populatedChunkedFileStore
    need_binary = isinstance(store.currentChunk, BinaryFileStore)
    for key in keys:
        value = getValue(key, need_binary)
        assert store.get(str(key).encode() if need_binary else str(key)) == value


def testSizeChunkedFileStore(populatedChunkedFileStore):
    """
    Check performance of `numKeys`
    """
    s = perf_counter()
    c1 = sum(1 for _ in populatedChunkedFileStore.iterator())
    e = perf_counter()
    t1 = e - s
    s = perf_counter()
    c2 = populatedChunkedFileStore.numKeys
    e = perf_counter()
    t2 = e - s
    # It should be faster to use ChunkedFileStore specific implementation
    # of `numKeys`
    assert t1 > t2
    assert c1 == c2
    assert c2 == dataSize


def testIterateOverChunkedFileStore(populatedChunkedFileStore):
    store = populatedChunkedFileStore
    m = data(need_binary=isinstance(store.currentChunk, BinaryFileStore))
    for k, v in store.iterator():
        assert m[int(k)-1] == v


def test_get_range(populatedChunkedFileStore):
    # Test for range spanning multiple chunks

    # Range begins and ends at chunk boundaries
    store = populatedChunkedFileStore
    m = data(need_binary=isinstance(store.currentChunk, BinaryFileStore))
    num = 0
    for k, v in populatedChunkedFileStore.get_range(chunkSize+1, 2*chunkSize):
        assert m[int(k) - 1] == v
        num += 1
    assert num == chunkSize

    # Range does not begin or end at chunk boundaries
    num = 0
    for k, v in populatedChunkedFileStore.get_range(chunkSize+2, 2*chunkSize+1):
        assert m[int(k) - 1] == v
        num += 1
    assert num == chunkSize

    # Range spans multiple full chunks
    num = 0
    for k, v in populatedChunkedFileStore.get_range(chunkSize + 2,
                                                    5 * chunkSize + 1):
        assert m[int(k) - 1] == v
        num += 1
    assert num == 4*chunkSize

    with pytest.raises(AssertionError):
        list(populatedChunkedFileStore.get_range(5, 1))

    for frm, to in [(i, j) for i, j in itertools.permutations(
            range(1, dataSize+1), 2) if i <= j]:
        for k, v in populatedChunkedFileStore.get_range(frm, to):
            assert m[int(k) - 1] == v


def test_chunk_size_limitation_when_default_file_used(tmpdir):
    """
    This test checks that chunk size can not be lower then a number of items 
    in default file, used for initialization of ChunkedFileStore
    """

    isLineNoKey = True
    storeContentHash = False
    ensureDurability = True
    dbDir = str(tmpdir)
    defaultFile = os.path.join(dbDir, "template")

    lines = [
        "FirstLine\n",
        "OneMoreLine\n",
        "AnotherLine\n",
        "LastDefaultLine\n"
    ]
    with open(defaultFile, "w") as f:
        f.writelines(lines)

    chunkSize = len(lines) - 1

    with pytest.raises(ValueError) as err:
        ChunkedFileStore(dbDir=dbDir,
                         dbName="chunked_data",
                         isLineNoKey=isLineNoKey,
                         storeContentHash=storeContentHash,
                         chunkSize=chunkSize,
                         ensureDurability=ensureDurability,
                         chunkStoreConstructor=TextFileStore,
                         defaultFile=defaultFile)
    assert "Default file is larger than chunk size" in str(err)
