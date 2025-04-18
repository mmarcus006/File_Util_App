from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Table1(BaseModel):
    """
    Table 1: Systemwide Outlet Summary. Rows contain values corresponding to the 'columns' list.
    """
    title: Optional[str] = Field(
        None, description="Optional: Full title of Table 1"
    )
    columns: List[str] = Field(
        description="Defines the order of values in each row array for Table 1"
    )
    rows: List[List[Union[str, int, float, None]]] = Field(
        description="Data rows as arrays. Each element corresponds to the 'columns' definition"
    )


class Table2(BaseModel):
    """
    Table 2: Transfers. Rows contain values corresponding to the 'columns' list.
    """
    title: Optional[str] = Field(
        None, description="Optional: Full title of Table 2"
    )
    columns: List[str] = Field(
        description="Defines the order of values in each row array for Table 2"
    )
    rows: List[List[Union[str, int, float, None]]] = Field(
        description="Data rows as arrays"
    )


class Table3(BaseModel):
    """
    Table 3: Status of Franchised/Licensed Outlets. Rows correspond to 'columns'.
    """
    title: Optional[str] = Field(
        None, description="Optional: Full title of Table 3"
    )
    columns: List[str] = Field(
        description="Defines the order of values in each row array for Table 3"
    )
    rows: List[List[Union[str, int, float, None]]] = Field(
        description="Data rows as arrays"
    )


class Table4(BaseModel):
    """
    Table 4: Status of Company-Owned Outlets. Rows correspond to 'columns'.
    """
    title: Optional[str] = Field(
        None, description="Optional: Full title of Table 4"
    )
    columns: List[str] = Field(
        description="Defines the order of values in each row array for Table 4"
    )
    rows: List[List[Union[str, int, float, None]]] = Field(
        description="Data rows as arrays"
    )


class Table5(BaseModel):
    """
    Table 5: Projected Openings. Rows correspond to 'columns'.
    """
    title: Optional[str] = Field(
        None, description="Optional: Full title of Table 5"
    )
    columns: List[str] = Field(
        description="Defines the order of values in each row array for Table 5"
    )
    rows: List[List[Union[str, int, float, None]]] = Field(
        description="Data rows as arrays"
    )


class Item20FranchiseTables(BaseModel):
    """
    Schema for franchise tables data containing information about outlets, 
    transfers, franchise status, company-owned outlets, and projected openings.
    """
    t1: Optional[Table1] = Field(
        None, description="Table 1: Systemwide Outlet Summary"
    )
    t2: Optional[Table2] = Field(
        None, description="Table 2: Transfers"
    )
    t3: Optional[Table3] = Field(
        None, description="Table 3: Status of Franchised/Licensed Outlets"
    )
    t4: Optional[Table4] = Field(
        None, description="Table 4: Status of Company-Owned Outlets"
    )
    t5: Optional[Table5] = Field(
        None, description="Table 5: Projected Openings"
    ) 