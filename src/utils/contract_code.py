from dotenv import load_dotenv
import os
import requests
import json
import re

# Load environment variables
load_dotenv()

def fetch_contract_source_code(account_address: str):
    """
    Fetch contract source code from the BaseScan API.
    If that fails, attempt to fetch the contract code using Covalent’s API.
    Then iterate over each file (key in 'sources'), skipping OpenZeppelin/library imports,
    and return only the main contract's Solidity code.
    """
    print("I am inside fetch_contract_source_code")

    try:
        # Attempt using BaseScan API
        api_key = os.environ.get("ETHERSCAN_API_KEY")
        if not api_key:
            raise Exception("ETHERSCAN_API_KEY not set in environment")
        url = f"https://api.basescan.org/api?module=contract&action=getsourcecode&address={account_address}&apikey={api_key}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "1":
            raise Exception(f"API error! message: {data.get('message')}")

        # Typically the first and only item in "result"
        result = data.get("result", [{}])[0]
        raw_source = result.get("SourceCode", "")
        contract_name = result.get("ContractName", "")
        print("contract_name:", contract_name)

        # Process the raw_source (e.g., JSON encoded with multiple files)
        main_contract_code = extract_main_contract(raw_source, contract_name)
        return {"success": True, "data": main_contract_code}

    except Exception as error:
        print("Failed to fetch contract source code using BaseScan API:", error)
        print("Attempting to fetch contract source code using Covalent API...")

        try:
            covalent_api_key = os.environ.get("COVALENT_API_KEY")
            if not covalent_api_key:
                raise Exception("COVALENT_API_KEY not set in environment")
            # Assuming the Base chain id is 8453. Adjust if needed.
            chain_id = "8453"
            covalent_url = f"https://api.covalenthq.com/v1/{chain_id}/address/{account_address}/contract_metadata/?key={covalent_api_key}"
            response = requests.get(covalent_url)
            response.raise_for_status()

            data = response.json()
            items = data.get("data", {}).get("items", [])
            if not items:
                raise Exception("No contract metadata found from Covalent")
            # Use the first item from the returned list
            contract_metadata = items[0].get("contract_metadata", {})
            source_code = contract_metadata.get("source_code")
            if not source_code:
                raise Exception("No source code found in Covalent contract metadata")
            
            # Process the source code. If the Covalent API returns JSON-encoded source code,
            # the extract_main_contract function can process it.
            main_contract_code = extract_main_contract(source_code, "")
            return {"success": True, "data": main_contract_code}

        except Exception as covalent_error:
            print("Failed to fetch contract source code from Covalent API:", covalent_error)
            return {"success": False, "error": str(covalent_error)}

def extract_main_contract(raw_source: str, contract_name: str) -> list:
    """
    1. Attempt to parse raw_source as JSON.
    2. If we have a "sources" dict, iterate over each key.
    3. Skip any key that suggests it's an imported library (e.g. contains '@openzeppelin').
    4. Return the content(s) for the "main" contract file(s) in a list.
    """
    try:
        # Remove wrapping quotes if necessary and parse as JSON
        # (Assumes the raw_source is wrapped in extra quotes)
        raw_source = json.loads(raw_source[1:-1])
        if not raw_source or "sources" not in raw_source:
            return []

        sources = raw_source["sources"]
        contract_contents = []
        for key, value in sources.items():
            # Optionally, skip library files (e.g., those containing '@openzeppelin')
            if '@openzeppelin' in key:
                continue
            if contract_name and contract_name not in key:
                continue
            contract_contents.append(value.get("content", ""))
        return contract_contents
    except Exception as e:
        print("Error in extract_main_contract:", e)
        return []

# # Example usage:
# if __name__ == "__main__":
#     # Replace with a valid contract address on Base.
#     contract_address = "0xYourContractAddressHere"
#     result = fetch_contract_source_code(contract_address)
#     print(result)
