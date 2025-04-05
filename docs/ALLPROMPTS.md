## 5. Gemini API Prompts

**Core Instructions (Included in ALL Prompts):**

```text
You are an expert financial data extraction assistant. You will receive the full content of a single bank statement converted to Markdown format. Your task is to meticulously extract the specified financial data points covering the *entire* statement period and return them ONLY as a single, valid JSON object matching the provided Pydantic model schema below.

**Input:** Markdown content of the bank statement.

**Output:** Respond ONLY with a JSON object matching this Pydantic schema:

```json
{/* Insert the JSON Schema derived from the StatementData Pydantic model here */}
```

**Extraction Guidelines:**

1.  **Completeness:** Extract all available holdings and transactions listed for the statement period.
2.  **Accuracy:** Ensure numerical values (prices, quantities, amounts, dates) are extracted precisely as they appear. Pay close attention to decimal places.
3.  **Dates:** Extract dates in YYYY-MM-DD format. If only Month/Day/Year is given, convert it.
4.  **Amounts:** Ensure `net_amount` in transactions is negative for debits/withdrawals/purchases and positive for credits/deposits/sales/income.
5.  **Holdings:** Extract all listed securities under relevant sections (Equity, Fixed Income, Cash Equivalents, etc.). If cost basis or unrealized gain/loss is missing, use `null`. Determine `unrealized_gain_loss_term` ('Short', 'Long', 'Mixed') if indicated (e.g., ST/LT markers) or if derivable from tax lot info if present, otherwise use `null`. Yields/Rates should be extracted as percentages (e.g., 5.0 for 5.0%).
6.  **Transactions:** Extract all activity listed. Map the activity description to a standard `transaction_type` (e.g., 'Buy', 'Sell', 'Dividend', 'Interest', 'Withdrawal', 'Deposit', 'Fee', 'Reinvestment', 'Transfer In', 'Transfer Out'). Extract `security_description`, `ticker_symbol`, and `cusip` if associated with the transaction. For cash-only transactions (Withdrawal, Deposit, Fee, Interest without security), `security_description` can be null or describe the transaction. Extract per-transaction `realized_gain_loss` and `realized_gain_loss_term` ONLY if explicitly shown on the transaction line item itself (common on some sale confirmations, less common in activity summaries).
7.  **Tax Summary:** Extract Period and YTD values where available. If a value (e.g., Tax-Exempt Interest YTD) is not present in the summary section, use `null`.
8.  **Cash Balances:** Extract the summary `beginning_cash_balance` and `ending_cash_balance` which typically represent combined cash/sweep/MMF balances shown in cash flow or activity summaries. Do not sum individual cash/MMF holdings for these fields.
9.  **Missing Data:** If a specific field required by the schema is not found in the statement, represent it as `null` in the JSON output. Do not make up data.
10. **JSON Only:** Your entire response must be ONLY the JSON object, starting with `{` and ending with `}`. Do not include any introductory text, explanations, or markdown formatting around the JSON.
```

**Bank-Specific Prompt Additions:**

**(Append these sections AFTER the Core Instructions and BEFORE the Markdown Content)**

**A. JPMorgan Chase (JPM) Specific Instructions:**

```text
**JPMorgan Chase Specific Hints:**

*   **Institution Name:** Set to "JPMorgan Chase".
*   **Account Info:** Find Account Number in "Account Summary" table or "ACCT." in "Asset Account" header. Account Holder Name is usually under these headers.
*   **Statement Period:** Look for "For the Period M/D/YY to M/D/YY".
*   **Statement Summary:** Use "Account Summary" (Consolidated or Asset Account). "Beginning/Ending Net Market Value", "Change In Value". Find `net_contributions_withdrawals_period` under "Portfolio Activity" (Current Period Value).
*   **Cash Balances:** Use "Portfolio Activity Summary" -> "Beginning/Ending Cash Balance".
*   **Tax Summary:** Use "Tax Summary" section. Extract Period and YTD values for Taxable Income (derive interest), Tax-Exempt Income, Dividends, Realized Gain/Loss (Short/Long Term).
*   **Holdings:** Look under "Equity Detail", "Cash & Fixed Income Detail". "Price", "Value", "Adjusted Tax Cost", "Unrealized Gain/Loss". Ticker is labeled "TICKER:", CUSIP/ID is labeled "ID:". Term for Unrealized G/L might need inference from tax lots if not directly labeled. "Est. Annual Inc.", "Yield". "Accrued Div./Interest".
*   **Transactions:** Look under "Portfolio Activity Detail". "Settle Date" is primary date. Map "Type" column to `transaction_type`. "Amount" is `net_amount`. Check sale transactions for 'L' indicator for `realized_gain_loss_term` and calculate `realized_gain_loss` from Proceeds (Amount) vs Tax Cost (need cost basis lookup or info if provided on line).
```

**B. Morgan Stanley (MS) Specific Instructions:**

```text
**Morgan Stanley Specific Hints:**

*   **Institution Name:** Set to "Morgan Stanley".
*   **Account Info:** Find Account Number ("Active Assets Account") in header. Account Holder Name under "STATEMENT FOR:".
*   **Statement Period:** Look for "For the Period Month D-D, YYYY".
*   **Statement Summary:** Use "Account Summary" (Page 3/4). "Beginning/Ending Total Value", "Change in Value". Calculate `net_contributions_withdrawals_period` from Period's Cash Flow activity if not directly stated.
*   **Cash Balances:** Use "CASH FLOW" -> "OPENING/CLOSING CASH, BDP, MMFs".
*   **Tax Summary:** Use "INCOME AND DISTRIBUTION SUMMARY" and "GAIN/(LOSS) SUMMARY" (Page 4). Extract Period ("This Period") and YTD ("This Year") values for Interest, Tax-Exempt Income, Other Dividends, Short-Term Gain, Long-Term Gain. Sum ST/LT Gain for Total Realized G/L.
*   **Holdings:** Look under "STOCKS", "EXCHANGE-TRADED & CLOSED-END FUNDS", "GOVERNMENT SECURITIES", "MUTUAL FUNDS". "Share Price"/"Unit Price", "Market Value", "Total Cost"/"Adj Total Cost", "Unrealized Gain/(Loss)". Ticker is usually in parentheses "(XXX)". CUSIP may be present for some fixed income. "ST"/"LT" often shown next to Unrealized G/L. "Est Ann Income", "Current Yield %". Accrued Interest might be in summary or fixed income details.
*   **Transactions:** Look under "CASH FLOW ACTIVITY BY DATE" (Page 9). "Activity Date" is primary date, "Settlement Date" is also available. Map "Activity Type" to `transaction_type`. "Credits/(Debits)" column is `net_amount` (ensure Debits are negative). Realized G/L per transaction is generally not shown here.
```

**C. Goldman Sachs (GS) Specific Instructions:**

```text
**Goldman Sachs Specific Hints:**

*   **Institution Name:** Set to "Goldman Sachs".
*   **Account Info:** Find Account Number ("Portfolio No:") on Page 1. Account Holder Name is at the top left.
*   **Statement Period:** Look for "Period Covering Month DD, YYYY to Month DD, YYYY" or "Period Ended...".
*   **Statement Summary:** Use "Overview" (Page 3). Find "MARKET VALUE AS OF [Start/End Date]", "CHANGE IN MARKET VALUE". Find `net_contributions_withdrawals_period` under "INVESTMENT RESULTS" -> "Net Deposits (Withdrawals)" (Current Month).
*   **Cash Balances:** Use "Cash Activity" (Page 7) -> "CLOSING BALANCE AS OF [Previous/Current Period End Date]".
*   **Tax Summary:** Use "US Tax Summary" (Page 4) and/or "Tax Details" (Page 9). Extract Period ("Current Month") and YTD ("Year to date" or "Quarter to Date" - use YTD if available) values for Corporate Interest, Bank Interest (sum for Taxable Interest), Dividends Received. Realized G/L summaries might appear here if sales occurred, extract if present.
*   **Holdings:** Look under "Holdings" (Page 5), e.g., "PUBLIC EQUITY", "CASH, DEPOSITS & MONEY MARKET FUNDS". "Market Price"/"Unit Price", "Market Value", "Adjusted Cost/Original Cost"/"Cost Basis", "Unrealized Gain (Loss)". Ticker is usually in parentheses "(XXX)". CUSIP may be present. Term for Unrealized G/L likely in "Tax Lots" (Page 10), use if needed, otherwise null. "Estimated Annual Income", "Current Yield". "Accrued Income".
*   **Transactions:** Look under "Investment Activity" (Page 6) and "Cash Activity" (Page 7), "Deposits and Withdrawals" (Page 11). "Effective Date" or "Process Date" is primary date. Map descriptions to `transaction_type`. "Amount" is `net_amount` (ensure withdrawals/debits are negative). Realized G/L per transaction is generally not shown here.
```

**Final Prompt Structure (Example for JPM):**

```text
[Core Instructions]

[JPMorgan Chase Specific Hints]

**Markdown Content:**

[Insert Full Markdown Content of the JPM Statement Here]
```

---