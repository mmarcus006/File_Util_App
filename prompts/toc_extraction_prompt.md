Please analyze the following text extracted from the Table of Contents page(s) of a Franchise Disclosure Document (FDD).

Your task is to identify all 23 standard FDD Items and any listed Exhibits (e.g., Exhibit A, Exhibit B, etc.). The standard FDD Items are:

1.  The Franchisor and any Parents, Predecessors, and Affiliates
2.  Business Experience
3.  Litigation
4.  Bankruptcy
5.  Initial Fees
6.  Other Fees
7.  Estimated Initial Investment
8.  Restrictions on Sources of Products and Services
9.  Franchisee's Obligations
10. Financing
11. Franchisor's Assistance, Advertising, Computer Systems, and Training
12. Territory
13. Trademarks
14. Patents, Copyrights, and Proprietary Information
15. Obligation to Participate in the Actual Operation of the Franchise Business
16. Restrictions on What the Franchisee May Sell
17. Renewal, Termination, Transfer, and Dispute Resolution
18. Public Figures
19. Financial Performance Representations
20. Outlets and Franchisee Information
21. Financial Statements
22. Contracts
23. Receipts

For each item and exhibit found in the text provided below, extract:
1.  The full, exact title as it appears in the text (this may slightly differ from the standard list above).
2.  The corresponding page number, if available. If no page number is clearly associated with an item in the text, the value for `page_number` should be `null`.

Format your response STRICTLY as a JSON object conforming to the `FDDStructure` schema, which contains a list (`items`) of `FDDItem` objects. Each `FDDItem` object must have `item_name` (string) and `page_number` (integer or null).

Example JSON Output Format:
```json
{
  "items": [
    {
      "item_name": "Item 1: The Franchisor and any Parents, Predecessors, and Affiliates",
      "page_number": 5
    },
    {
      "item_name": "Item 2: Business Experience",
      "page_number": 8
    },
    {
      "item_name": "Item 19: Financial Performance Representations",
      "page_number": null
    },
    {
      "item_name": "Item 23: Receipts",
      "page_number": 95
    },
    {
      "item_name": "Exhibit A: Franchise Agreement",
      "page_number": 100
    },
    {
      "item_name": "Exhibit B: Sample Lease",
      "page_number": 120
    }
  ]
}
```

Ensure all standard 23 items and all listed exhibits are captured if present in the text provided below.

--- FDD Table of Contents Text --- 