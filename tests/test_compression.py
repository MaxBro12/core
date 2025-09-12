from compression import Compressor


def test_compression_decompression():
    test_string = "Lorem aca ici rnan/n/trfet/rgkee1234567890!@#$%^&*()_+-="
    compression = Compressor()

    compressed_test = compression.compress_zstd_str(test_string)
    assert len(compressed_test) <= len(test_string)
    decompression = compression.decompress_zstd_str(compressed_test)
    assert str(test_string) == str(decompression)
