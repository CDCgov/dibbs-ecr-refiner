from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class IcdCrosswalk(SQLModel, table=True):
    """
    Model representing ICD-9 to ICD-10 code crosswalk mappings.

    SQLModel table for storing relationships between ICD-9 and ICD-10 codes
    along with their matching flags from the GEM mappings.

    Attributes:
        id: Primary key for the crosswalk entry.
        icd10_code: ICD-10 code linked to concept.gem_formatted_code.
        icd9_code: Corresponding ICD-9 code.
        match_flags: Flags indicating the type of code match.
    """

    id: int | None = Field(default=None, primary_key=True)
    icd10_code: str = Field(default=None, foreign_key="concept.gem_formatted_code")
    icd9_code: str
    match_flags: str


class ConditionConceptLink(SQLModel, table=True):
    """Junction table linking conditions to concepts.

    Implements many-to-many relationship between Condition and Concept tables.

    Attributes:
        concept_id: Foreign key referencing concept.id.
        condition_id: Foreign key referencing condition.id.
    """

    concept_id: int | None = Field(
        default=None, foreign_key="concept.id", primary_key=True
    )
    condition_id: int | None = Field(
        default=None, foreign_key="condition.id", primary_key=True
    )


class Concept(SQLModel, table=True):
    """
    Model representing clinical concepts from terminology services.

    Stores concept information including codes, names, and relationships
    to concept types and conditions.

    Attributes:
        id: Primary key for the concept.
        name: Concept name (nullable as some TES concepts lack names).
        code: Original concept code.
        gem_formatted_code: Code formatted for GEM mappings.
        system: Code system identifier.
        types: Related concept types (one-to-many).
        conditions: Related conditions (many-to-many).
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str | None  # Some concepts in TES have a NULL name
    code: str
    gem_formatted_code: str
    system: str

    types: list["ConceptType"] = Relationship(back_populates="concept")
    conditions: list["Condition"] = Relationship(
        back_populates="concepts", link_model=ConditionConceptLink
    )

    __table_args__ = (UniqueConstraint("code", "system"),)

    def __eq__(self, other):
        """
        Two concepts are equal if they have the same code and system.
        """

        if isinstance(other, self.__class__):
            return self.code == other.code and self.system == other.system
        return NotImplemented

    def __hash__(self):
        """
        Hashes the concept based on the code and system.
        """

        return hash((self.code, self.system))


class ConceptType(SQLModel, table=True):
    """
    Model representing types or categories of clinical concepts.

    Stores type classifications for concepts with a one-to-many
    relationship back to the Concept table.

    Attributes:
        id: Primary key for the concept type.
        type: Type classification (nullable).
        concept_id: Foreign key to parent concept.
        concept: Related concept (one-to-many back-reference).
    """

    id: int | None = Field(default=None, primary_key=True)
    type: str | None
    concept_id: int = Field(foreign_key="concept.id")

    concept: Concept = Relationship(back_populates="types")


class Condition(SQLModel, table=True):
    """
    Model representing clinical conditions or diagnoses.

    Stores condition information and maintains relationships with
    associated concepts through the ConditionConceptLink table.

    Attributes:
        id: Primary key for the condition.
        name: Condition name.
        code: Condition code (indexed).
        system: Code system identifier.
        version: Version of the code system.
        concepts: Related concepts (many-to-many).
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str
    code: str = Field(index=True)
    system: str
    version: str

    concepts: list["Concept"] = Relationship(
        back_populates="conditions", link_model=ConditionConceptLink
    )

    __table_args__ = (UniqueConstraint("code", "system"),)

    def __eq__(self, other):
        """
        Two conditions are equal if they have the same code and system.
        """

        if isinstance(other, self.__class__):
            return self.code == other.code and self.system == other.system
        return NotImplemented

    def __hash__(self):
        """
        Hashes the condition based on the code and system.
        """

        return hash((self.code, self.system))
