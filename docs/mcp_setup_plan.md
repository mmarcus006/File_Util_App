# Plan: Configure Supabase MCP Server Connection

1.  **Identify Target File:** The file to be modified is `../../Users/mille/AppData/Roaming/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`.
2.  **Retrieve Access Token:** Use the provided PAT: `sbp_29b85e257f9e1b2dc80008b3c3b047ef4d9f1972`.
3.  **Determine OS Configuration:** Use the Windows-specific command structure provided in the initial instructions.
4.  **Construct New Configuration:** Create the JSON snippet for the Supabase server using the PAT.
    ```json
    "supabase": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "@supabase/mcp-server-supabase@latest",
        "--access-token",
        "sbp_29b85e257f9e1b2dc80008b3c3b047ef4d9f1972"
      ]
    }
    ```
5.  **Prepare Final File Content:** Integrate the new configuration into the existing `mcp_settings.json` content. The final content will be:
    ```json
    {
      "mcpServers": {
        "supabase": {
          "command": "cmd",
          "args": [
            "/c",
            "npx",
            "-y",
            "@supabase/mcp-server-supabase@latest",
            "--access-token",
            "sbp_29b85e257f9e1b2dc80008b3c3b047ef4d9f1972"
          ]
        }
      }
    }
    ```
6.  **Implementation:** Switch to 'code' mode to use the `write_to_file` tool to update `mcp_settings.json` with the final content above.
7.  **User Actions:** Remind the user of the necessary manual steps after the file is updated:
    *   Ensure Node/NPM/NPX are correctly configured in the system PATH.
    *   Restart VS Code for the changes to take effect.

**Diagram (Conceptual Flow):**

```mermaid
graph TD
    A[Start: User Request] --> B{Gather Info: PAT, File Path, OS};
    B --> C[Construct Supabase JSON Config];
    C --> D[Prepare Final mcp_settings.json Content];
    D --> E{User Review & Approval};
    E -- Approved --> F[Switch to Code Mode];
    F --> G[Write Updated mcp_settings.json];
    G --> H[User: Verify PATH & Restart VSCode];
    H --> I[End: MCP Server Connected];
    E -- Changes Requested --> B;