from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from aiohttp import ClientSession, ClientTimeout, ClientResponseError
from fake_useragent import FakeUserAgent
from colorama import *
from dotenv import load_dotenv
import asyncio, random, json, time, os

# Muat variabel dari file .env
load_dotenv()

class Faroswap:
    def __init__(self) -> None:
        self.HEADERS = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://faroswap.xyz",
            "Referer": "https://faroswap.xyz/",
            "User-Agent": FakeUserAgent().random
        }
        # Membaca semua konfigurasi dari file .env
        self.RPC_URL = os.getenv("RPC_URL")
        self.DODO_API_KEY = os.getenv("DODO_API_KEY")
        self.EXPLORER_URL = os.getenv("EXPLORER_URL")
        self.PHRS_CONTRACT_ADDRESS = os.getenv("PHRS_CONTRACT_ADDRESS")
        self.WPHRS_CONTRACT_ADDRESS = os.getenv("WPHRS_CONTRACT_ADDRESS")
        self.USDC_CONTRACT_ADDRESS = os.getenv("USDC_CONTRACT_ADDRESS")
        self.USDT_CONTRACT_ADDRESS = os.getenv("USDT_CONTRACT_ADDRESS")
        self.WETH_CONTRACT_ADDRESS = os.getenv("WETH_CONTRACT_ADDRESS")
        self.WBTC_CONTRACT_ADDRESS = os.getenv("WBTC_CONTRACT_ADDRESS")
        self.MIXSWAP_ROUTER_ADDRESS = os.getenv("MIXSWAP_ROUTER_ADDRESS")
        self.DVM_ROUTER_ADDRESS = os.getenv("DVM_ROUTER_ADDRESS")
        self.POOL_ROUTER_ADDRESS = os.getenv("POOL_ROUTER_ADDRESS")
        
        self.TICKERS = ["PHRS", "WPHRS", "USDC", "USDT", "WETH", "WBTC"]
        self.ERC20_CONTRACT_ABI = json.loads('''[{"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},{"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},{"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]},{"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]},{"type":"function","name":"deposit","stateMutability":"payable","inputs":[],"outputs":[]},{"type":"function","name":"withdraw","stateMutability":"nonpayable","inputs":[{"name":"wad","type":"uint256"}],"outputs":[]}]''')
        self.UNISWAP_V2_CONTRACT_ABI = [{"type":"function","name":"addDVMLiquidity","stateMutability":"payable","inputs":[{"internalType":"address","name":"dvmAddress","type":"address"},{"internalType":"uint256","name":"baseInAmount","type":"uint256"},{"internalType":"uint256","name":"quoteInAmount","type":"uint256"},{"internalType":"uint256","name":"baseMinAmount","type":"uint256"},{"internalType":"uint256","name":"quoteMinAmount","type":"uint256"},{"internalType":"uint8","name":"flag","type":"uint8"},{"internalType":"uint256","name":"deadLine","type":"uint256"}],"outputs":[{"internalType":"uint256","name":"shares","type":"uint256"},{"internalType":"uint256","name":"baseAdjustedInAmount","type":"uint256"},{"internalType":"uint256","name":"quoteAdjustedInAmount","type":"uint256"}]}]

        # === KONFIGURASI OTOMATIS ===
        self.dp_or_wd_option = 3  # 1: Deposit, 2: Withdraw, 3: Skip
        self.deposit_amount = 0.01
        self.withdraw_amount = 0.01

        self.swap_count = 15  # << ANDA BISA UBAH NILAI INI
        self.phrs_swap_amount = 0.01
        self.wphrs_swap_amount = 0.01
        self.usdc_swap_amount = 0.01
        self.usdt_swap_amount = 0.01
        self.weth_swap_amount = 0.000001
        self.wbtc_swap_amount = 0.0000001

        self.add_lp_count = 5
        self.usdc_add_lp_amount = 0.01
        self.usdt_add_lp_amount = 0.01
        
        self.min_delay = 10
        self.max_delay = 25
        # ============================

    def log(self, message):
        print(f"{Fore.CYAN+Style.BRIGHT}[+]{Style.RESET_ALL} {message}", flush=True)

    def welcome(self):
        print(f"\n{Fore.GREEN+Style.BRIGHT}Faroswap{Fore.BLUE+Style.BRIGHT} Auto BOT (Full-Auto, Single Run)\n"
              f"{Fore.GREEN+Style.BRIGHT}Rey? {Fore.YELLOW+Style.BRIGHT}<INI WATERMARK>\n")
    
    def load_pools(self):
        filename = "pools.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return None
            with open(filename, 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
            
    def generate_address(self, account: str):
        try:
            return Account.from_key(account).address
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Generate Address Failed: {e}{Style.RESET_ALL}")
            return None
            
    def mask_account(self, account):
        return f"{account[:6]}******{account[-6:]}" if account else None

    def generate_swap_option(self):
        valid_pairs = [(f, t) for f in self.TICKERS for t in self.TICKERS if f != t and (f,t) != ("PHRS", "WPHRS") and (f,t) != ("WPHRS", "PHRS")]
        from_ticker, to_ticker = random.choice(valid_pairs)
        from_token = getattr(self, f"{from_ticker}_CONTRACT_ADDRESS")
        to_token = getattr(self, f"{to_ticker}_CONTRACT_ADDRESS")
        amount = getattr(self, f"{from_ticker.lower()}_swap_amount")
        return {"swap_option": f"{from_ticker} to {to_ticker}", "from_token": from_token, "to_token": to_token, "ticker": from_ticker, "amount": amount}
    
    def generate_lp_option(self):
        base_ticker, quote_ticker = random.sample(["USDC", "USDT"], 2)
        base_token = getattr(self, f"{base_ticker}_CONTRACT_ADDRESS")
        quote_token = getattr(self, f"{quote_ticker}_CONTRACT_ADDRESS")
        amount = getattr(self, f"{base_ticker.lower()}_add_lp_amount")
        return {"lp_option": f"{base_ticker} to {quote_ticker}", "base_token": base_token, "quote_token": quote_token, "base_ticker": base_ticker, "quote_ticker": quote_ticker, "amount": amount}
        
    async def get_web3_with_check(self, retries=3, timeout=60):
        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs={"timeout": timeout}))
                if web3.is_connected():
                    return web3
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
        raise ConnectionError("Failed to connect to RPC after several retries.")
            
    async def get_token_balance(self, address: str, contract_address: str):
        try:
            web3 = await self.get_web3_with_check()
            if contract_address == self.PHRS_CONTRACT_ADDRESS:
                balance, decimals = web3.eth.get_balance(address), 18
            else:
                token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
                balance = token_contract.functions.balanceOf(address).call()
                decimals = token_contract.functions.decimals().call()
            return balance / (10 ** decimals)
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Get Balance Failed: {e}{Style.RESET_ALL}")
            return None
            
    async def wait_for_receipt(self, web3, tx_hash, timeout=300):
        return await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=timeout)
            
    async def perform_transaction(self, tx_function, account, address, value=0):
        try:
            web3 = await self.get_web3_with_check()
            tx_count = web3.eth.get_transaction_count(address, "pending")
            max_priority_fee = web3.to_wei(1, 'gwei')
            
            estimated_gas = tx_function.estimate_gas({'from': address, 'value': value})
            tx = tx_function.build_transaction({'from': address, 'value': value, 'gas': int(estimated_gas * 1.5), 'maxFeePerGas': max_priority_fee, 'maxPriorityFeePerGas': max_priority_fee, 'nonce': tx_count, 'chainId': web3.eth.chain_id})
            
            signed_tx = web3.eth.account.sign_transaction(tx, account)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = await self.wait_for_receipt(web3, tx_hash)
            return web3.to_hex(tx_hash), receipt.blockNumber
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Transaction Failed: {e}{Style.RESET_ALL}")
            return None, None

    async def perform_deposit(self, account: str, address: str):
        web3 = await self.get_web3_with_check()
        contract = web3.eth.contract(address=web3.to_checksum_address(self.WPHRS_CONTRACT_ADDRESS), abi=self.ERC20_CONTRACT_ABI)
        amount_to_wei = web3.to_wei(self.deposit_amount, "ether")
        return await self.perform_transaction(contract.functions.deposit(), account, address, value=amount_to_wei)
        
    async def perform_withdraw(self, account: str, address: str):
        web3 = await self.get_web3_with_check()
        contract = web3.eth.contract(address=web3.to_checksum_address(self.WPHRS_CONTRACT_ADDRESS), abi=self.ERC20_CONTRACT_ABI)
        amount_to_wei = web3.to_wei(self.withdraw_amount, "ether")
        return await self.perform_transaction(contract.functions.withdraw(amount_to_wei), account, address)
    
    async def approving_token(self, account: str, address: str, router_address: str, asset_address: str, amount_to_wei: int):
        try:
            web3 = await self.get_web3_with_check()
            spender = web3.to_checksum_address(router_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(asset_address), abi=self.ERC20_CONTRACT_ABI)
            allowance = token_contract.functions.allowance(address, spender).call()
            
            if allowance < amount_to_wei:
                self.log(f"{Fore.YELLOW}Approving token...{Style.RESET_ALL}")
                tx_hash, block_number = await self.perform_transaction(token_contract.functions.approve(spender, 2**256 - 1), account, address)
                if tx_hash:
                    self.log_transaction("Approve", tx_hash, block_number)
                    await self.print_timer()
                    return True
                else:
                    raise Exception("Approval transaction failed to get hash.")
            return True
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Approving token failed: {e}{Style.RESET_ALL}")
            return False

    async def perform_swap(self, account: str, address: str, from_token: str, to_token: str, amount: float):
        try:
            web3 = await self.get_web3_with_check()
            decimals = 18 if from_token == self.PHRS_CONTRACT_ADDRESS else web3.eth.contract(address=web3.to_checksum_address(from_token), abi=self.ERC20_CONTRACT_ABI).functions.decimals().call()
            amount_to_wei = int(amount * (10 ** decimals))
            
            if from_token != self.PHRS_CONTRACT_ADDRESS:
                if not await self.approving_token(account, address, self.MIXSWAP_ROUTER_ADDRESS, from_token, amount_to_wei):
                    return None, None
            
            dodo_route = await self.get_dodo_route(address, from_token, to_token, amount_to_wei)
            if not dodo_route or "data" not in dodo_route: return None, None
            
            route_data = dodo_route["data"]
            tx_func = {'to': self.MIXSWAP_ROUTER_ADDRESS, 'from': address, 'data': route_data.get('data'), 'value': int(route_data.get('value'))}
            
            web3_instance = await self.get_web3_with_check()
            tx_func['nonce'] = web3_instance.eth.get_transaction_count(address, 'pending')
            tx_func['gas'] = await asyncio.to_thread(web3_instance.eth.estimate_gas, tx_func)
            tx_func.update({'maxFeePerGas': web3.to_wei(1, 'gwei'), 'maxPriorityFeePerGas': web3.to_wei(1, 'gwei'), 'chainId': web3.eth.chain_id})
            
            signed_tx = web3.eth.account.sign_transaction(tx_func, account)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = await self.wait_for_receipt(web3, tx_hash)
            return web3.to_hex(tx_hash), receipt.blockNumber
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Swap failed: {e}{Style.RESET_ALL}")
            return None, None
            
    async def perform_add_dvm_liquidity(self, account: str, address: str, pair_address: str, base_token: str, quote_token: str, amount: float):
        try:
            in_amount = int(amount * (10 ** 6))
            
            approve1_success = await self.approving_token(account, address, self.POOL_ROUTER_ADDRESS, base_token, in_amount)
            if not approve1_success:
                self.log(f"{Fore.RED}Approval for base token failed. Stopping.{Style.RESET_ALL}")
                return None, None

            approve2_success = await self.approving_token(account, address, self.POOL_ROUTER_ADDRESS, quote_token, in_amount)
            if not approve2_success:
                self.log(f"{Fore.RED}Approval for quote token failed. Stopping.{Style.RESET_ALL}")
                return None, None
            
            self.log(f"{Fore.YELLOW}Approvals successful. Adding liquidity...{Style.RESET_ALL}")
            await asyncio.sleep(5)

            web3 = await self.get_web3_with_check()
            contract = web3.eth.contract(address=web3.to_checksum_address(self.DVM_ROUTER_ADDRESS), abi=self.UNISWAP_V2_CONTRACT_ABI)
            add_lp_func = contract.functions.addDVMLiquidity(web3.to_checksum_address(pair_address), in_amount, in_amount, int(in_amount * 0.99), int(in_amount * 0.99), 0, int(time.time()) + 600)
            return await self.perform_transaction(add_lp_func, account, address)
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Add Liquidity Failed: {e}{Style.RESET_ALL}")
            return None, None

    async def print_timer(self):
        delay = random.randint(self.min_delay, self.max_delay)
        for i in range(delay, 0, -1):
            print(f"{Fore.CYAN+Style.BRIGHT}[+]{Style.RESET_ALL} {Fore.BLUE+Style.BRIGHT}Waiting {i}s for next tx...{Style.RESET_ALL}", end="\r", flush=True)
            await asyncio.sleep(1)
        print(" " * 80, end="\r")

    async def get_dodo_route(self, address: str, from_token: str, to_token: str, amount: int, retries=5):
        url = (f"https://api.dodoex.io/route-service/v2/widget/getdodoroute?chainId=688688&deadLine={int(time.time()) + 600}"
               f"&apikey={self.DODO_API_KEY}&slippage=3.225&source=dodoV2AndMixWasm&toTokenAddress={to_token}"
               f"&fromTokenAddress={from_token}&userAddr={address}&estimateGas=false&fromAmount={amount}")
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get(url=url, headers=self.HEADERS) as response:
                        response.raise_for_status()
                        result = await response.json()
                        if result.get("status") == 200: return result
                        raise ValueError(result.get("data", "Quote Not Available"))
            except Exception as e:
                self.log(f"{Fore.RED}Fetch Dodo Route Failed ({attempt+1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1: await asyncio.sleep(3)
        return None
    
    def log_transaction(self, action, tx_hash, block_number, final_log=False):
        if tx_hash:
            status, color, icon = "Success", Fore.GREEN, "[✓]"
            print(f"{color+Style.BRIGHT}{icon}{Style.RESET_ALL} {action} {status}")
            print(f"{color+Style.BRIGHT}   - Block:{Style.RESET_ALL} {Fore.WHITE}{block_number}{Style.RESET_ALL}")
            print(f"{color+Style.BRIGHT}   - Explorer:{Style.RESET_ALL} {Fore.WHITE}{self.EXPLORER_URL}/tx/{tx_hash}{Style.RESET_ALL}")
        else:
            status, color, icon = "Failed", Fore.RED, "[x]"
            print(f"{color+Style.BRIGHT}{icon}{Style.RESET_ALL} {action} {status}")

        if final_log:
            print("-" * 72)

    async def process_deposit(self, account, address):
        balance = await self.get_token_balance(address, self.PHRS_CONTRACT_ADDRESS)
        self.log(f"Balance: {balance or 0:.4f} PHRS | Amount to Deposit: {self.deposit_amount} PHRS")
        if balance and balance > self.deposit_amount:
            tx_hash, block = await self.perform_deposit(account, address)
            self.log_transaction("Deposit", tx_hash, block, True)
        else: self.log(f"{Fore.YELLOW}Insufficient PHRS balance.{Style.RESET_ALL}")

    async def process_withdraw(self, account, address):
        balance = await self.get_token_balance(address, self.WPHRS_CONTRACT_ADDRESS)
        self.log(f"Balance: {balance or 0:.4f} WPHRS | Amount to Withdraw: {self.withdraw_amount} WPHRS")
        if balance and balance > self.withdraw_amount:
            tx_hash, block = await self.perform_withdraw(account, address)
            self.log_transaction("Withdraw", tx_hash, block, True)
        else: self.log(f"{Fore.YELLOW}Insufficient WPHRS balance.{Style.RESET_ALL}")

    async def _execute_swap(self, swap_details, account, address):
        self.log(f"Option: {swap_details['swap_option']}")
        balance = await self.get_token_balance(address, swap_details['from_token'])
        self.log(f"Balance: {balance or 0:.4f} {swap_details['ticker']} | Amount to Swap: {swap_details['amount']} {swap_details['ticker']}")
        if balance and balance >= swap_details['amount']:
            tx_hash, block = await self.perform_swap(account, address, **{k:v for k,v in swap_details.items() if k in ['from_token', 'to_token', 'amount']})
            self.log_transaction("Swap", tx_hash, block)
            await self.print_timer()
        else:
            self.log(f"{Fore.YELLOW}Insufficient {swap_details['ticker']} balance.{Style.RESET_ALL}")

    # <<< DIUBAH: Logika perulangan diperbaiki
    async def process_swap(self, account, address):
        self.log(f"{Fore.MAGENTA}Starting Swap Module ({self.swap_count} transactions)...{Style.RESET_ALL}")
        
        if self.swap_count < 1:
            self.log(f"{Fore.YELLOW}Swap count is zero, skipping swap module.{Style.RESET_ALL}")
            print("-" * 72)
            return

        # 1. Fixed Swap: PHRS to WPHRS
        self.log(f"Executing Swap 1/{self.swap_count} (Fixed: PHRS -> WPHRS)")
        fixed_swap_details = {
            "swap_option": "PHRS to WPHRS",
            "from_token": self.PHRS_CONTRACT_ADDRESS,
            "to_token": self.WPHRS_CONTRACT_ADDRESS,
            "ticker": "PHRS",
            "amount": self.phrs_swap_amount
        }
        await self._execute_swap(fixed_swap_details, account, address)

        # 2. Loop untuk swap acak yang tersisa
        for i in range(1, self.swap_count):
            self.log(f"Executing Swap {i + 1}/{self.swap_count} (Random)")
            random_swap_details = self.generate_swap_option()
            await self._execute_swap(random_swap_details, account, address)
            
        print("-" * 72)

    async def process_add_liquidity(self, account, address):
        self.log(f"{Fore.MAGENTA}Starting Add Liquidity Module ({self.add_lp_count} transactions)...{Style.RESET_ALL}")
        if not self.pools:
            self.log(f"{Fore.RED}pools.json not loaded. Skipping liquidity operations.{Style.RESET_ALL}")
            return
            
        for i in range(self.add_lp_count):
            self.log(f"Executing Add Liquidity {i+1}/{self.add_lp_count}")
            lp_details = self.generate_lp_option()
            pair_addr = self.pools[0].get(f"{lp_details['base_ticker']}_{lp_details['quote_ticker']}")
            if not pair_addr:
                self.log(f"{Fore.RED}Pool address for {lp_details['lp_option']} not found.{Style.RESET_ALL}")
                continue
            
            self.log(f"Option: {lp_details['lp_option']}")
            base_bal = await self.get_token_balance(address, lp_details['base_token'])
            quote_bal = await self.get_token_balance(address, lp_details['quote_token'])
            self.log(f"Balances: {base_bal or 0:.4f} {lp_details['base_ticker']}, {quote_bal or 0:.4f} {lp_details['quote_ticker']} | Amount: {lp_details['amount']}")

            if base_bal and quote_bal and base_bal > lp_details['amount'] and quote_bal > lp_details['amount']:
                tx_hash, block = await self.perform_add_dvm_liquidity(account, address, pair_addr, **{k:v for k,v in lp_details.items() if k in ['base_token', 'quote_token', 'amount']})
                self.log_transaction("Add Liquidity", tx_hash, block)
                await self.print_timer()
            else:
                self.log(f"{Fore.YELLOW}Insufficient token balance for liquidity.{Style.RESET_ALL}")
        print("-" * 72)

    async def main(self):
        account = os.getenv("PRIVATE_KEY")
        if not account or not account.strip():
            self.log(f"{Fore.RED+Style.BRIGHT}Error: PRIVATE_KEY not found or is empty in .env file.{Style.RESET_ALL}")
            return

        os.system('cls' if os.name == 'nt' else 'clear')
        self.welcome()
        
        self.pools = self.load_pools()
        address = self.generate_address(account)
        
        separator = "=" * 25
        self.log(f"{Fore.CYAN+Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                 f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                 f"{Fore.CYAN+Style.BRIGHT}]{separator}{Style.RESET_ALL}")

        if not address:
            self.log(f"{Fore.RED+Style.BRIGHT}Invalid Private Key. Please check your .env file.{Style.RESET_ALL}")
            return

        if self.dp_or_wd_option == 1: await self.process_deposit(account, address)
        elif self.dp_or_wd_option == 2: await self.process_withdraw(account, address)
        
        await self.process_swap(account, address)
        await self.process_add_liquidity(account, address)
        
        self.log(f"{Fore.GREEN+Style.BRIGHT}Cycle completed. The script will now exit.{Style.RESET_ALL}")
        self.log(f"{Fore.CYAN+Style.BRIGHT}={Style.RESET_ALL}"*72)

if __name__ == "__main__":
    try:
        bot = Faroswap()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED+Style.BRIGHT}[ EXITING ] User interrupted the process.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED+Style.BRIGHT}[ FATAL ERROR ] An unexpected error occurred: {e}{Style.RESET_ALL}")
