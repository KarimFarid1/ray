from typing import TypeVar, List, Generic, Iterator, Any, Union, Optional, \
    TYPE_CHECKING

if TYPE_CHECKING:
    import pandas
    import pyarrow
    from ray.experimental.data.impl.block_builder import BlockBuilder

from ray.util.annotations import DeveloperAPI

T = TypeVar("T")

# Represents a batch of rows to be stored in the Ray object store.
#
# Block data can be accessed in a uniform way via ``BlockAccessors`` such as
# ``SimpleBlockAccessor`` and ``ArrowBlockAccessor``.
Block = Union[List[T], "pyarrow.Table"]


@DeveloperAPI
class BlockMetadata:
    """Metadata about the block.

    Attributes:
        num_rows: The number of rows contained in this block, or None.
        size_bytes: The approximate size in bytes of this block, or None.
        schema: The pyarrow schema or types of the block elements, or None.
        input_files: The list of file paths used to generate this block, or
            the empty list if indeterminate.
    """

    def __init__(self, *, num_rows: Optional[int], size_bytes: Optional[int],
                 schema: Union[type, "pyarrow.lib.Schema"],
                 input_files: List[str]):
        if input_files is None:
            input_files = []
        self.num_rows: Optional[int] = num_rows
        self.size_bytes: Optional[int] = size_bytes
        self.schema: Optional[Any] = schema
        self.input_files: List[str] = input_files


@DeveloperAPI
class BlockAccessor(Generic[T]):
    """Provides accessor methods for a specific block.

    Ideally, we wouldn't need a separate accessor classes for blocks. However,
    this is needed if we want to support storing ``pyarrow.Table`` directly
    as a top-level Ray object, without a wrapping class (issue #17186).

    There are two types of block accessors: ``SimpleBlockAccessor``, which
    operates over a plain Python list, and ``ArrowBlockAccessor``, for
    ``pyarrow.Table`` type blocks.
    """

    def num_rows(self) -> int:
        """Return the number of rows contained in this block."""
        raise NotImplementedError

    def iter_rows(self) -> Iterator[T]:
        """Iterate over the rows of this block."""
        raise NotImplementedError

    def slice(self, start: int, end: int, copy: bool) -> Block:
        """Return a slice of this block.

        Args:
            start: The starting index of the slice.
            end: The ending index of the slice.
            copy: Whether to perform a data copy for the slice.

        Returns:
            The sliced block result.
        """
        raise NotImplementedError

    def to_pandas(self) -> "pandas.DataFrame":
        """Convert this block into a Pandas dataframe."""
        raise NotImplementedError

    def to_arrow_table(self) -> "pyarrow.Table":
        """Convert this block into an Arrow table."""
        raise NotImplementedError

    def size_bytes(self) -> int:
        """Return the approximate size in bytes of this block."""
        raise NotImplementedError

    def schema(self) -> Union[type, "pyarrow.lib.Schema"]:
        """Return the Python type or pyarrow schema of this block."""
        raise NotImplementedError

    def get_metadata(self, input_files: List[str]) -> BlockMetadata:
        """Create a metadata object from this block."""
        return BlockMetadata(
            num_rows=self.num_rows(),
            size_bytes=self.size_bytes(),
            schema=self.schema(),
            input_files=input_files)

    @staticmethod
    def builder() -> "BlockBuilder[T]":
        """Create a builder for this block type."""
        raise NotImplementedError

    @staticmethod
    def for_block(block: Block) -> "BlockAccessor[T]":
        """Create a block accessor for the given block."""
        import pyarrow

        if isinstance(block, pyarrow.Table):
            from ray.experimental.data.impl.arrow_block import \
                ArrowBlockAccessor
            return ArrowBlockAccessor(block)
        elif isinstance(block, list):
            from ray.experimental.data.impl.block_builder import \
                SimpleBlockAccessor
            return SimpleBlockAccessor(block)
        else:
            raise TypeError("Not a block type: {}".format(block))
