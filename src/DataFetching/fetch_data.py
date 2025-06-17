"""
MLBB Draft Assistant - Data Fetching Module

This module provides functionality to fetch hero counter and compatibility data
from the Mobile Legends: Bang Bang (MLBB) API.

Author: MLBB Draft Assistant Team
Date: June 17, 2025
"""

import requests
import json
import os
import argparse
import sys
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv


class MatchType(Enum):
    """Enumeration for different match types in MLBB."""
    COUNTER = "0"
    COMPATIBILITY = "1"


class RankType(Enum):
    """Enumeration for different rank types in MLBB."""
    ALL_RANK = "101"     # All ranks
    EPIC_RANK = "5"      # Epic rank
    LEGEND_RANK = "6"    # Legend rank
    MYTHIC_RANK = "7"    # Mythic rank (default)
    HONOR_RANK = "8"     # Honor rank
    GLORY_RANK = "9"     # Glory rank


@dataclass
class APIFilter:
    """Data class representing an API filter for MLBB requests."""
    field: str
    operator: str
    value: Union[str, int]


@dataclass
class APIPayload:
    """Data class representing the complete API payload structure."""
    pageSize: int
    filters: List[APIFilter]
    sorts: List[Any]
    pageIndex: int


@dataclass
class APIResponse:
    """Data class representing the API response structure."""
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    status_code: int


class MLBBDataFetcher:
    """
    A professional class for fetching MLBB hero data including counters and compatibility.
    
    This class provides methods to interact with the MLBB API to retrieve
    hero counter relationships and compatibility data for draft assistance.
    Features URL encryption for security.
    
    Attributes:
        base_url (str): The base URL for MLBB API endpoints (encrypted)
        default_headers (Dict[str, str]): Default headers for API requests
        timeout (int): Request timeout in seconds
        max_retries (int): Maximum number of retry attempts
    """
    
    # Class constants (encrypted URL and endpoint)
    BASE_URL: str = "Z0FBQUFBQm9VWnBveXdRZC0xb3lvUXpSdGxDSFk4RjJ6bllkM19pT0VVQV9SUDNuQVZlaHJkYXZzaWtManVzcG0xSllrNTc3Ul90ZGkwdFFXeFZVYTVaMjI5NG1JSFc0TS1xcmxMVmdYSlEzQ3RMZ1dxcFdaYmdYVFhEdmxBcEd6bkRnZG1OTlVlV20="
    API_ENDPOINT: str = "Z0FBQUFBQm9VWnV3aldFUExOQThvVlRJWHgyenpkZDJ6STlBYW5uUU94bG9CU0tuN2NFbzUyMEdIb3d4T2ZOdzhYSHE2Z3NEeHhpTnBOeFdkUDJuWmdpSUphN0VGOTJDOTlSRkxmUnB3WW9mZDhYOGsxZnFnOEE9"
    MIN_HERO_ID: int = 1
    MAX_HERO_ID: int = 128
    DEFAULT_PAGE_SIZE: int = 20
    DEFAULT_PAGE_INDEX: int = 1
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    def __init__(
        self,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        data_directory: str = "data"
    ) -> None:
        """
        Initialize the MLBB Data Fetcher.
        
        Args:
            timeout (int): Request timeout in seconds. Defaults to 30.
            max_retries (int): Maximum retry attempts. Defaults to 3.
            data_directory (str): Base directory for saving data files. Defaults to "data".
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize encryption and decrypt URL
        self.encryption_key = self._load_encryption_key()
        self.base_url = self._decrypt_string(self.BASE_URL)
        self.api_endpoint = self._decrypt_string(self.API_ENDPOINT)

        self.timeout = timeout
        self.max_retries = max_retries
        self.data_directory = Path(data_directory)
        self.default_headers = {'Content-Type': 'application/json'}
        
        # Setup logging first
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Create data directories if they don't exist
        self._ensure_data_directories()
    
    def _load_encryption_key(self) -> bytes:
        """
        Load and derive encryption key from environment variable.
        
        Returns:
            bytes: Fernet-compatible encryption key
            Raises:
                ValueError: If KEY environment variable is not set
        """
        key_string = os.getenv('KEY')
        if not key_string:
            raise ValueError("KEY environment variable not set. Please set KEY in .env file.")
        
        # Derive a proper Fernet key from the password
        password = key_string.encode()
        salt = b'mlbb_draft_assistant_salt'  # Fixed salt for consistency
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _decrypt_string(self, encrypted_string: str) -> str:
        """
        Decrypt an encrypted string using the encryption key.
        
        Args:
            encrypted_string (str): The base64 encoded encrypted string.

        Returns:
            str: Decrypted string
            
        Raises:
            Exception: If decryption fails
        """
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_string.encode())
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"Failed to decrypt string: {str(e)}")
            # It's good practice to be more specific about the error if possible
            # For example, distinguish between decoding errors and decryption errors
            raise ValueError("Failed to decrypt string. Check your encryption key or the encrypted string format.")

    @staticmethod
    def encrypt_url(url: str, key: bytes) -> str:
        """
        Encrypt a URL for secure storage.
        
        Args:
            url (str): URL to encrypt
            key (bytes): Encryption key
            
        Returns:
            str: Base64 encoded encrypted URL
        """
        fernet = Fernet(key)
        encrypted_url = fernet.encrypt(url.encode())
        return base64.urlsafe_b64encode(encrypted_url).decode()
    
    def _validate_hero_id(self, hero_id: int) -> bool:
        """
        Validate if the hero ID is within the acceptable range.
        
        Args:
            hero_id (int): The hero ID to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValueError: If hero_id is not within valid range
        """
        if not isinstance(hero_id, int):
            raise ValueError(f"Hero ID must be an integer, got {type(hero_id)}")
        
        if not (self.MIN_HERO_ID <= hero_id <= self.MAX_HERO_ID):
            raise ValueError(
                f"Hero ID must be between {self.MIN_HERO_ID} and {self.MAX_HERO_ID}, "
                f"got {hero_id}"
            )
        
        return True
    
    def _setup_logger(self) -> None:
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _ensure_data_directories(self) -> None:
        """
        Create necessary data directories if they don't exist.
        
        Creates:
            - data/hero_counter/
            - data/hero_compatibility/
        """
        counter_dir = self.data_directory / "hero_counter"
        compatibility_dir = self.data_directory / "hero_compatibility"
        
        counter_dir.mkdir(parents=True, exist_ok=True)
        compatibility_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Data directories ensured: {counter_dir}, {compatibility_dir}")
    
    def _save_to_file(
        self,
        data: Dict[str, Any],
        hero_id: int,
        data_type: str
    ) -> bool:
        """
        Save fetched data to JSON file.
        
        Args:
            data (Dict[str, Any]): The data to save
            hero_id (int): The hero ID for filename
            data_type (str): Either "counter" or "compatibility"
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            if data_type == "counter":
                file_path = self.data_directory / "hero_counter" / f"{hero_id}.json"
            elif data_type == "compatibility":
                file_path = self.data_directory / "hero_compatibility" / f"{hero_id}.json"
            else:
                self.logger.error(f"Invalid data_type: {data_type}")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data saved to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save data to file: {str(e)}")
            return False
    
    def _build_payload(
        self,
        main_hero_id: int,
        match_type: MatchType,
        rank_type: RankType,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_index: int = DEFAULT_PAGE_INDEX
    ) -> APIPayload:
        """
        Build the API payload for MLBB data requests.
        
        Args:
            main_hero_id (int): The main hero ID (1-128)
            match_type (MatchType): Type of match data to fetch
            rank_type (RankType): Rank type filter
            page_size (int): Number of results per page
            page_index (int): Page index for pagination
            
        Returns:
            APIPayload: Structured payload for the API request
        """
        filters = [
            APIFilter(field="match_type", operator="eq", value=match_type.value),
            APIFilter(field="main_heroid", operator="eq", value=str(main_hero_id)),
            APIFilter(field="bigrank", operator="eq", value=rank_type.value)
        ]
        
        return APIPayload(
            pageSize=page_size,
            filters=filters,
            sorts=[],
            pageIndex=page_index
        )
    
    def _build_headers(self, language: str = "en") -> Dict[str, str]:
        """
        Build request headers with optional language specification.
        
        Args:
            language (str): Language code for localization. Defaults to "en".
            
        Returns:
            Dict[str, str]: Complete headers dictionary
        """
        headers = self.default_headers.copy()
        if language and language != "en":
            headers['x-lang'] = language
        
        return headers
    
    def _make_request(
        self,
        payload: APIPayload,
        headers: Dict[str, str]
    ) -> APIResponse:
        """
        Make HTTP request to MLBB API with retry logic.
        
        Args:
            payload (APIPayload): The request payload
            headers (Dict[str, str]): Request headers
            
        Returns:
            APIResponse: Structured API response
        """
        url = f"{self.base_url}{self.api_endpoint}"
        
        # Convert payload to dict for JSON serialization
        payload_dict = {
            "pageSize": payload.pageSize,
            "filters": [
                {
                    "field": f.field,
                    "operator": f.operator,
                    "value": f.value
                } for f in payload.filters
            ],
            "sorts": payload.sorts,
            "pageIndex": payload.pageIndex
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Making API request (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    url,
                    json=payload_dict,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return APIResponse(
                        success=True,
                        data=response.json(),
                        error_message=None,
                        status_code=response.status_code
                    )
                else:
                    error_msg = f"API returned status {response.status_code}: {response.text}"
                    self.logger.warning(error_msg)
                    
                    return APIResponse(
                        success=False,
                        data=None,
                        error_message=error_msg,
                        status_code=response.status_code
                    )
                    
            except (ConnectionError, Timeout) as e:
                last_exception = e
                self.logger.warning(f"Network error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    continue
                    
            except RequestException as e:
                last_exception = e
                self.logger.error(f"Request error: {str(e)}")
                break
        
        # If we get here, all retries failed
        error_msg = f"All {self.max_retries} attempts failed. Last error: {str(last_exception)}"
        self.logger.error(error_msg)
        
        return APIResponse(
            success=False,
            data=None,
            error_message=error_msg,
            status_code=0
        )
    
    def get_hero_counters(
        self,
        main_hero_id: int,
        language: str = "en",
        page_size: int = DEFAULT_PAGE_SIZE,
        page_index: int = DEFAULT_PAGE_INDEX,
        rank: str = "7"
    ) -> APIResponse:
        """
        Fetch hero counter data for a specific hero.
        
        This method retrieves information about which heroes counter
        the specified main hero, including win rates and statistical data.
        
        Args:
            main_hero_id (int): The hero ID to get counters for (1-128)
            language (str): Language code for localization. Defaults to "en"
            page_size (int): Number of results per page. Defaults to 20
            page_index (int): Page index for pagination. Defaults to 1
            rank (str): Rank filter value ("101"=All, "5"=Epic, "6"=Legend, "7"=Mythic, "8"=Honor, "9"=Glory). Defaults to "7"
            
        Returns:
            APIResponse: Response containing counter data or error information
            
        Raises:
            ValueError: If hero_id is not within valid range (1-128)
            
        Example:
            >>> fetcher = MLBBDataFetcher()
            >>> response = fetcher.get_hero_counters(main_hero_id=50, rank="7")
            >>> if response.success:
            ...     print("Counter data:", response.data)
            ... else:
            ...     print("Error:", response.error_message)
        """
        self._validate_hero_id(main_hero_id)
        
        self.logger.info(f"Fetching hero counters for hero ID: {main_hero_id} with rank: {rank}")
        
        # Select appropriate rank type
        rank_map = {
            "101": RankType.ALL_RANK,
            "5": RankType.EPIC_RANK,
            "6": RankType.LEGEND_RANK,
            "7": RankType.MYTHIC_RANK,
            "8": RankType.HONOR_RANK,
            "9": RankType.GLORY_RANK
        }
        rank_type = rank_map.get(rank, RankType.MYTHIC_RANK)
        
        payload = self._build_payload(
            main_hero_id=main_hero_id,
            match_type=MatchType.COUNTER,
            rank_type=rank_type,
            page_size=page_size,
            page_index=page_index
        )
        
        headers = self._build_headers(language)
        
        response = self._make_request(payload, headers)
        
        # Save data to file if request was successful
        if response.success and response.data:
            self._save_to_file(response.data, main_hero_id, "counter")
        
        return response
    
    def get_hero_compatibility(
        self,
        main_hero_id: int,
        language: str = "en",
        page_size: int = DEFAULT_PAGE_SIZE,
        page_index: int = DEFAULT_PAGE_INDEX,
        rank: str = "7"
    ) -> APIResponse:
        """
        Fetch hero compatibility data for a specific hero.
        
        This method retrieves information about which heroes work well
        together with the specified main hero, including synergy statistics.
        
        Args:
            main_hero_id (int): The hero ID to get compatibility for (1-128)
            language (str): Language code for localization. Defaults to "en"
            page_size (int): Number of results per page. Defaults to 20
            page_index (int): Page index for pagination. Defaults to 1
            rank (str): Rank filter value ("101"=All, "5"=Epic, "6"=Legend, "7"=Mythic, "8"=Honor, "9"=Glory). Defaults to "7"
            
        Returns:
            APIResponse: Response containing compatibility data or error information
            
        Raises:
            ValueError: If hero_id is not within valid range (1-128)
            
        Example:
            >>> fetcher = MLBBDataFetcher()
            >>> response = fetcher.get_hero_compatibility(main_hero_id=75, rank="7")
            >>> if response.success:
            ...     print("Compatibility data:", response.data)
            ... else:
            ...     print("Error:", response.error_message)
        """
        self._validate_hero_id(main_hero_id)
        
        self.logger.info(f"Fetching hero compatibility for hero ID: {main_hero_id} with rank: {rank}")
        
        # Select appropriate rank type
        rank_map = {
            "101": RankType.ALL_RANK,
            "5": RankType.EPIC_RANK,
            "6": RankType.LEGEND_RANK,
            "7": RankType.MYTHIC_RANK,
            "8": RankType.HONOR_RANK,
            "9": RankType.GLORY_RANK
        }
        rank_type = rank_map.get(rank, RankType.MYTHIC_RANK)
        
        payload = self._build_payload(
            main_hero_id=main_hero_id,
            match_type=MatchType.COMPATIBILITY,
            rank_type=rank_type,
            page_size=page_size,
            page_index=page_index
        )
        
        headers = self._build_headers(language)
        
        response = self._make_request(payload, headers)
        
        # Save data to file if request was successful
        if response.success and response.data:
            self._save_to_file(response.data, main_hero_id, "compatibility")
        
        return response
    
    def get_bulk_hero_data(
        self,
        hero_ids: List[int],
        data_type: str = "both",
        language: str = "en"
    ) -> Dict[int, Dict[str, APIResponse]]:
        """
        Fetch data for multiple heroes in bulk.
        
        Args:
            hero_ids (List[int]): List of hero IDs to fetch data for
            data_type (str): Type of data to fetch ("counters", "compatibility", "both")
            language (str): Language code for localization
            
        Returns:
            Dict[int, Dict[str, APIResponse]]: Nested dictionary with hero_id -> data_type -> response
            
        Raises:
            ValueError: If any hero_id is invalid or data_type is not recognized
        """
        if data_type not in ["counters", "compatibility", "both"]:
            raise ValueError("data_type must be 'counters', 'compatibility', or 'both'")
        
        results = {}
        
        for hero_id in hero_ids:
            self._validate_hero_id(hero_id)
            results[hero_id] = {}
            
            if data_type in ["counters", "both"]:
                results[hero_id]["counters"] = self.get_hero_counters(hero_id, language)
            
            if data_type in ["compatibility", "both"]:
                results[hero_id]["compatibility"] = self.get_hero_compatibility(hero_id, language)
        
        return results
    
    def fetch_and_save_all_heroes(
        self,
        data_type: str = "both",
        language: str = "en",
        start_hero_id: int = 1,
        end_hero_id: int = 128,
        rank: str = "7"
    ) -> Dict[str, Dict[int, bool]]:
        """
        Fetch and save data for all heroes from start_hero_id to end_hero_id.
        
        Args:
            data_type (str): Type of data to fetch ("counters", "compatibility", "both")
            language (str): Language code for localization
            start_hero_id (int): Starting hero ID (inclusive). Defaults to 1.
            end_hero_id (int): Ending hero ID (inclusive). Defaults to 128.
            rank (str): Rank filter value ("101"=All, "5"=Epic, "6"=Legend, "7"=Mythic, "8"=Honor, "9"=Glory). Defaults to "7"
            
        Returns:
            Dict[str, Dict[int, bool]]: Results showing success/failure for each hero and data type
            
        Example:
            >>> fetcher = MLBBDataFetcher()
            >>> results = fetcher.fetch_and_save_all_heroes(rank="7")
            >>> print(f"Counter data saved for {sum(results['counters'].values())} heroes")
        """
        if data_type not in ["counters", "compatibility", "both"]:
            raise ValueError("data_type must be 'counters', 'compatibility', or 'both'")
        
        results = {"counters": {}, "compatibility": {}}
        total_heroes = end_hero_id - start_hero_id + 1
        
        self.logger.info(f"Starting bulk fetch for heroes {start_hero_id}-{end_hero_id} ({total_heroes} heroes)")
        
        for hero_id in range(start_hero_id, end_hero_id + 1):
            try:
                self.logger.info(f"Processing hero {hero_id}/{end_hero_id}")
                
                if data_type in ["counters", "both"]:
                    counter_response = self.get_hero_counters(hero_id, language, rank=rank)
                    results["counters"][hero_id] = counter_response.success
                    
                    if counter_response.success:
                        self.logger.info(f"✓ Hero {hero_id} counter data saved")
                    else:
                        self.logger.warning(f"✗ Hero {hero_id} counter data failed: {counter_response.error_message}")
                
                if data_type in ["compatibility", "both"]:
                    compatibility_response = self.get_hero_compatibility(hero_id, language, rank=rank)
                    results["compatibility"][hero_id] = compatibility_response.success
                    
                    if compatibility_response.success:
                        self.logger.info(f"✓ Hero {hero_id} compatibility data saved")
                    else:
                        self.logger.warning(f"✗ Hero {hero_id} compatibility data failed: {compatibility_response.error_message}")
                        
            except Exception as e:
                self.logger.error(f"Error processing hero {hero_id}: {str(e)}")
                if data_type in ["counters", "both"]:
                    results["counters"][hero_id] = False
                if data_type in ["compatibility", "both"]:
                    results["compatibility"][hero_id] = False
        
        # Summary
        if data_type in ["counters", "both"]:
            counter_success = sum(results["counters"].values())
            self.logger.info(f"Counter data: {counter_success}/{total_heroes} heroes successful")
        
        if data_type in ["compatibility", "both"]:
            compatibility_success = sum(results["compatibility"].values())
            self.logger.info(f"Compatibility data: {compatibility_success}/{total_heroes} heroes successful")
        
        return results


def parse_count_argument(count_arg: str) -> tuple[int, int]:
    """
    Parse the count argument to determine start and end hero IDs.
    
    Args:
        count_arg (str): Count argument ("all", single number, or range like "4-9")
        
    Returns:
        tuple[int, int]: (start_hero_id, end_hero_id)
        
    Raises:
        ValueError: If the count argument format is invalid
    """
    if count_arg.lower() == "all":
        return 1, 128
    elif "-" in count_arg:
        try:
            start, end = map(int, count_arg.split("-"))
            if start < 1 or end > 128 or start > end:
                raise ValueError(f"Invalid range: {count_arg}. Must be between 1-128 and start <= end")
            return start, end
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid range format: {count_arg}. Use format like '4-9'")
            raise
    else:
        try:
            hero_id = int(count_arg)
            if hero_id < 1 or hero_id > 128:
                raise ValueError(f"Hero ID must be between 1 and 128, got {hero_id}")
            return hero_id, hero_id
        except ValueError:
            raise ValueError(f"Invalid count argument: {count_arg}. Use 'all', single number, or range like '4-9'")


def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Setup command-line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="MLBB Draft Assistant - Fetch hero counter and compatibility data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch counter data for all heroes with Mythic rank (default)
  python src/DataFetching/fetch_data.py --select counter --count all --rank 7
  
  # Fetch compatibility data for hero 1 with Glory rank
  python src/DataFetching/fetch_data.py --select compatibility --count 1 --rank 9
  
  # Fetch both types for heroes 4-9 with Epic rank
  python src/DataFetching/fetch_data.py --select both --count 4-9 --rank 5
  
  # Fetch both types for hero 50 with all ranks
  python src/DataFetching/fetch_data.py --select both --count 50 --rank 101
  
  # Fetch counter data for heroes 10-20 with Legend rank
  python src/DataFetching/fetch_data.py --select counter --count 10-20 --rank 6

Rank Values:
  101 = All Ranks
  5   = Epic Rank
  6   = Legend Rank  
  7   = Mythic Rank (default)
  8   = Honor Rank
  9   = Glory Rank
        """
    )
    
    parser.add_argument(
        "--select",
        choices=["counter", "compatibility", "both"],
        required=True,
        help="Type of data to fetch (counter/compatibility/both)"
    )
    
    parser.add_argument(
        "--count",
        required=True,
        help="Heroes to fetch: 'all' for all heroes (1-128), single number (e.g., '1'), or range (e.g., '4-9')"
    )
    
    parser.add_argument(
        "--rank",
        choices=["101", "5", "6", "7", "8", "9"],
        default="7",
        help="Rank filter: 101=All, 5=Epic, 6=Legend, 7=Mythic (default), 8=Honor, 9=Glory"
    )
    
    parser.add_argument(
        "--lang",
        default="en",
        help="Language code for localization. Default: en"
    )
    
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory to save data files. Default: data"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds. Default: 30"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for failed requests. Default: 3"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main():
    """
    Main function for command-line interface.
    """
    parser = setup_cli_parser()
    args = parser.parse_args()
    
    # Setup logging level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Parse count argument
        start_hero_id, end_hero_id = parse_count_argument(args.count)
        
        # Map select argument to internal format
        data_type_map = {
            "counter": "counters",
            "compatibility": "compatibility",
            "both": "both"
        }
        data_type = data_type_map[args.select]
        
        # Initialize fetcher
        fetcher = MLBBDataFetcher(
            timeout=args.timeout,
            max_retries=args.max_retries,
            data_directory=args.data_dir
        )
        
        # Display execution plan
        hero_count = end_hero_id - start_hero_id + 1
        rank_names = {
            "101": "All Ranks",
            "5": "Epic Rank",
            "6": "Legend Rank", 
            "7": "Mythic Rank",
            "8": "Honor Rank",
            "9": "Glory Rank"
        }
        rank_display = f"{args.rank} ({rank_names.get(args.rank, 'Unknown')})"
        
        print(f"🚀 MLBB Data Fetcher Starting...")
        print(f"📊 Data Type: {args.select}")
        print(f"🎯 Heroes: {start_hero_id}-{end_hero_id} ({hero_count} heroes)")
        print(f"📈 Rank: {rank_display}")
        print(f"🌐 Language: {args.lang}")
        print(f"📁 Data Directory: {args.data_dir}")
        print(f"⏱️  Timeout: {args.timeout}s")
        print(f"🔄 Max Retries: {args.max_retries}")
        print("-" * 50)
        
        # Execute fetching
        results = fetcher.fetch_and_save_all_heroes(
            data_type=data_type,
            language=args.lang,
            start_hero_id=start_hero_id,
            end_hero_id=end_hero_id,
            rank=args.rank
        )
        
        # Display results summary
        print("\n" + "=" * 50)
        print("📊 EXECUTION SUMMARY")
        print("=" * 50)
        
        total_requests = 0
        total_successful = 0
        
        for data_name, hero_results in results.items():
            if hero_results:  # Only show if we have results for this data type
                successful = sum(hero_results.values())
                total = len(hero_results)
                success_rate = (successful / total * 100) if total > 0 else 0
                
                print(f"📋 {data_name.capitalize()}:")
                print(f"   ✅ Successful: {successful}/{total} ({success_rate:.1f}%)")
                
                if successful < total:
                    failed_heroes = [hero_id for hero_id, success in hero_results.items() if not success]
                    print(f"   ❌ Failed Heroes: {failed_heroes}")
                
                total_requests += total
                total_successful += successful
        
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        print(f"\n🎯 Overall Success Rate: {total_successful}/{total_requests} ({overall_success_rate:.1f}%)")
        
        if total_successful == total_requests:
            print("🎉 All requests completed successfully!")
        elif total_successful > 0:
            print("⚠️  Some requests failed. Check logs for details.")
        else:
            print("💥 All requests failed. Check your network connection and API endpoint.")
        
        print(f"📁 Data saved to: {Path(args.data_dir).absolute()}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    """
    Main entry point - supports both CLI and direct usage.
    """
    if len(sys.argv) > 1:
        # CLI mode - arguments provided
        main()
    else:
        # Direct execution mode - run examples
        print("🎯 MLBB Data Fetcher - Example Mode")
        print("=" * 50)
        print("No CLI arguments provided. Running examples...")
        print("\nFor CLI usage, run:")
        print("python src/DataFetching/fetch_data.py --help")
        print("\nRunning example fetches...")
        print("-" * 50)
        
        # Initialize the fetcher
        fetcher = MLBBDataFetcher()
        
        # Example 1: Get and save hero counters for a single hero
        print("\n=== Single Hero Counter Example ===")
        counter_response = fetcher.get_hero_counters(main_hero_id=1, rank="7")
        if counter_response.success:
            print("✓ Successfully fetched and saved counter data for hero 1")
            print(f"Status Code: {counter_response.status_code}")
            print("Data saved to: data/hero_counter/1.json")
        else:
            print("✗ Failed to fetch counter data")
            print(f"Error: {counter_response.error_message}")
        
        # Example 2: Get and save hero compatibility for a single hero
        print("\n=== Single Hero Compatibility Example ===")
        compatibility_response = fetcher.get_hero_compatibility(main_hero_id=1, rank="7")
        if compatibility_response.success:
            print("✓ Successfully fetched and saved compatibility data for hero 1")
            print(f"Status Code: {compatibility_response.status_code}")
            print("Data saved to: data/hero_compatibility/1.json")
        else:
            print("✗ Failed to fetch compatibility data")
            print(f"Error: {compatibility_response.error_message}")
        
        print("\n" + "=" * 50)
        print("📋 CLI USAGE EXAMPLES")
        print("=" * 50)
        print("# Fetch counter data for all heroes with Mythic rank (default):")
        print("python src/DataFetching/fetch_data.py --select counter --count all --rank 7")
        print()
        print("# Fetch compatibility data for hero 1 with Glory rank:")
        print("python src/DataFetching/fetch_data.py --select compatibility --count 1 --rank 9")
        print()
        print("# Fetch both types for heroes 4-9 with Epic rank:")
        print("python src/DataFetching/fetch_data.py --select both --count 4-9 --rank 5")
        print()
        print("# Fetch both types for hero 50 with all ranks:")
        print("python src/DataFetching/fetch_data.py --select both --count 50 --rank 101")
        print()
        print("# Fetch counter data for heroes 10-20 with Legend rank:")
        print("python src/DataFetching/fetch_data.py --select counter --count 10-20 --rank 6")
        print()
        print("# Show help:")
        print("python src/DataFetching/fetch_data.py --help")
        print()
        print("🏆 RANK OPTIONS:")
        print("  101 = All Ranks")
        print("  5   = Epic Rank")
        print("  6   = Legend Rank")
        print("  7   = Mythic Rank (default)")
        print("  8   = Honor Rank")
        print("  9   = Glory Rank")