from dotenv import load_dotenv
import os
import requests
import json
import re

# Load environment variables
load_dotenv()

def fetch_contract_source_code(account_address: str):
    """
    Fetch contract source code from the *scan API. Then iterate over each file
    (key in 'sources'), skipping OpenZeppelin/library imports, and return only
    the main contract's Solidity code.
    """
    print("I am inside fetch_contract_source_code")

    try:
        api_key = os.environ.get("ETHERSCAN_API_KEY")
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

        # Handle the possibility that raw_source is a JSON-encoded string
        main_contract_code = extract_main_contract(raw_source, contract_name)

        return {"success": True, "data": main_contract_code}
    except Exception as error:
        print("Failed to fetch contract source code:", error)
        return {"success": False, "error": str(error)}


def extract_main_contract(raw_source: str, contract_name: str) -> str:
    """
    1. Attempt to parse raw_source as JSON.
    2. If we have a "sources" dict, iterate over each key.
    3. Skip any key that suggests it's an imported library (e.g. contains '@openzeppelin').
    4. Return the content(s) for the "main" contract file(s).
    """
    try:
        # print(raw_source)
        raw_source = json.loads(raw_source[1:-1])
        # iterate through k
        if not raw_source:
            return False

        if "sources" not in raw_source:
            return False  # Handle case where "sources" key is missing

        sources = raw_source["sources"]
        contract =[]
        for key in sources:
                if contract_name in key:
                    # print(key)
                    contract.append(sources[key]["content"])
                    
        # print(contract)                   
        # # print(json.loads(raw_source[1:-1])  )

        return contract
    except:
        return []
    
# # Example usage:
# if __name__ == "__main__":
#     # Replace with a valid Ethereum contract address.
#     contract_address = "0x4f9fd6be4a90f2620860d680c0d4d5fb53d1a825"
#     result = fetch_contract_source_code(contract_address)
#     print(result)
