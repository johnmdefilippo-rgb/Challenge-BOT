import math
import time
import uuid
import requests
import pandas as pd

from datetime import datetime, timedelta, timezone
from config import CONFIG, API_ENDPOINT, EASTERN_TZ


# ============================================================
# TOPSTEPX CLIENT
# ============================================================

class TopstepXClient:
    def __init__(self, username: str, api_key: str):
        self.username = username
        self.api_key = api_key
        self.token = None

    def authenticate(self):
        url = f"{API_ENDPOINT}/api/Auth/loginKey"

        payload = {
            "userName": self.username,
            "apiKey": self.api_key,
        }

        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()

        if not data.get("success") or not data.get("token"):
            raise RuntimeError(f"Authentication failed: {data}")

        self.token = data["token"]
        print("Authenticated successfully.")
        return self.token

    def headers(self):
        if not self.token:
            raise RuntimeError("Client is not authenticated.")

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "accept": "text/plain",
        }

    def search_contract(self, symbol: str, live: bool = False):
        url = f"{API_ENDPOINT}/api/Contract/search"

        payload = {
            "searchText": symbol,
            "live": live,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Contract search failed: {data}")

        contracts = data.get("contracts", [])

        if not contracts:
            raise RuntimeError(f"No contracts found for symbol: {symbol}")

        active_contracts = [
            contract for contract in contracts
            if contract.get("activeContract") is True
        ]

        if active_contracts:
            return active_contracts[0]

        return contracts[0]

    def retrieve_2m_bars(self, contract_id: str, live: bool, limit: int = 300):
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=limit * 2 + 20)

        url = f"{API_ENDPOINT}/api/History/retrieveBars"

        payload = {
            "contractId": contract_id,
            "live": live,
            "startTime": start_time.isoformat().replace("+00:00", "Z"),
            "endTime": end_time.isoformat().replace("+00:00", "Z"),
            "unit": 2,
            "unitNumber": 2,
            "limit": limit,
            "includePartialBar": False,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Retrieve bars failed: {data}")

        bars = data.get("bars", [])

        if not bars:
            raise RuntimeError("No historical bars returned.")

        df = pd.DataFrame(bars)

        df["t"] = pd.to_datetime(df["t"], utc=True)
        df = df.sort_values("t").reset_index(drop=True)

        df.rename(
            columns={
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            },
            inplace=True,
        )

        return df

    def place_market_order(
        self,
        account_id: int,
        contract_id: str,
        side: int,
        size: int,
        tp_ticks: int,
        sl_ticks: int | None = None,
    ):
        url = f"{API_ENDPOINT}/api/Order/place"

        payload = {
            "accountId": account_id,
            "contractId": contract_id,
            "type": 2,  # Market order
            "side": side,  # 0 = Buy, 1 = Sell
            "size": size,
            "limitPrice": None,
            "stopPrice": None,
            "trailPrice": None,
            "customTag": f"ema_atr_eval_bot_{uuid.uuid4().hex[:10]}",
            "takeProfitBracket": {
                "ticks": int(tp_ticks),
                "type": 1,
            },
        }

        if sl_ticks is not None:
            payload["stopLossBracket"] = {
                "ticks": int(sl_ticks),
                "type": 4,
            }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Order placement failed: {data}")

        return data

    def search_open_orders(self, account_id: int):
        url = f"{API_ENDPOINT}/api/Order/searchOpen"

        payload = {
            "accountId": account_id,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Open order search failed: {data}")

        return data.get("orders", [])

    def search_positions(self, account_id: int):
        url = f"{API_ENDPOINT}/api/Position/search"

        payload = {
            "accountId": account_id,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Position search failed: {data}")

        return data.get("positions", [])

    def get_open_position_for_contract(self, account_id: int, contract_id: str):
        positions = self.search_positions(account_id)

        for position in positions:
            if position.get("contractId") == contract_id:
                size = position.get("size", 0)

                if abs(size) > 0:
                    return position

        return None

    def has_open_orders_for_contract(self, account_id: int, contract_id: str):
        orders = self.search_open_orders(account_id)

        for order in orders:
            if order.get("contractId") == contract_id:
                return True

        return False

    def close_position(self, account_id: int, contract_id: str):
        url = f"{API_ENDPOINT}/api/Position/closeContract"

        payload = {
            "accountId": account_id,
            "contractId": contract_id,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Close position failed: {data}")

        return data

    def get_account_balance(self, account_id: int):
        """
        This may need a small adjustment depending on the actual account response.
        It checks common balance fields.
        """

        url = f"{API_ENDPOINT}/api/Account/search"

        payload = {
            "onlyActiveAccounts": True,
        }

        response = requests.post(
            url,
            json=payload,
            headers=self.headers(),
            timeout=15,
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Account search failed: {data}")

        accounts = data.get("accounts", [])

        for account in accounts:
            if int(account.get("id")) == int(account_id):
                for field in ["balance", "equity", "cashBalance"]:
                    if field in account and account[field] is not None:
                        return float(account[field])

                raise RuntimeError(
                    f"Account found, but no balance/equity/cashBalance field found: {account}"
                )

        raise RuntimeError(f"Account ID {account_id} was not found.")


# ============================================================
# INDICATORS
# ============================================================

def add_indicators(df: pd.DataFrame, ema_fast: int, ema_slow: int, atr_length: int):
    df = df.copy()

    df["ema_fast"] = df["close"].ewm(span=ema_fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=ema_slow, adjust=False).mean()

    previous_close = df["close"].shift(1)

    tr_1 = df["high"] - df["low"]
    tr_2 = (df["high"] - previous_close).abs()
    tr_3 = (df["low"] - previous_close).abs()

    df["true_range"] = pd.concat([tr_1, tr_2, tr_3], axis=1).max(axis=1)
    df["atr"] = df["true_range"].rolling(atr_length).mean()

    return df


# ============================================================
# STRATEGY
# ============================================================

def get_signal(df: pd.DataFrame):
    """
    Returns:
        "LONG"
        "SHORT"
        None
    """

    if len(df) < 30:
        return None

    previous = df.iloc[-2]
    current = df.iloc[-1]

    previous_above_both = (
        previous["close"] > previous["ema_fast"]
        and previous["close"] > previous["ema_slow"]
    )

    current_above_both = (
        current["close"] > current["ema_fast"]
        and current["close"] > current["ema_slow"]
    )

    previous_below_both = (
        previous["close"] < previous["ema_fast"]
        and previous["close"] < previous["ema_slow"]
    )

    current_below_both = (
        current["close"] < current["ema_fast"]
        and current["close"] < current["ema_slow"]
    )

    ema_bullish = current["ema_fast"] > current["ema_slow"]
    ema_bearish = current["ema_fast"] < current["ema_slow"]

    if current_above_both and not previous_above_both and ema_bullish:
        return "LONG"

    if current_below_both and not previous_below_both and ema_bearish:
        return "SHORT"

    return None


# ============================================================
# SIZING
# ============================================================

def contract_size_from_eval(evaluation_size: int, contracts_per_50k: int):
    blocks = max(1, math.floor(evaluation_size / 50000))
    return blocks * contracts_per_50k


def ticks_from_atr(atr: float, tick_size: float, multiplier: float):
    ticks = round((atr * multiplier) / tick_size)
    return max(1, int(ticks))


# ============================================================
# RISK MANAGER
# ============================================================

class RiskManager:
    def __init__(self, config):
        self.config = config
        self.trade_count_by_day = {}
        self.starting_balance_by_day = {}
        self.locked_out_by_day = {}
        self.last_flatten_date = None

    def now_et(self):
        return datetime.now(EASTERN_TZ)

    def today_key(self):
        return self.now_et().date().isoformat()

    def parse_time_today_et(self, hhmm: str):
        hour, minute = hhmm.split(":")
        now = self.now_et()

        return now.replace(
            hour=int(hour),
            minute=int(minute),
            second=0,
            microsecond=0,
        )

    def is_manual_paused(self):
        return bool(self.config.get("manual_pause", False))

    def is_inside_trading_hours(self):
        now = self.now_et()
        start = self.parse_time_today_et(self.config["trading_start_et"])
        end = self.parse_time_today_et(self.config["trading_end_et"])

        return start <= now <= end

    def is_after_no_new_trade_cutoff(self):
        now = self.now_et()
        cutoff = self.parse_time_today_et(self.config["no_new_trades_after_et"])

        return now >= cutoff

    def should_flatten_now(self):
        if not self.config.get("flatten_at_end_of_day", False):
            return False

        now = self.now_et()
        today = now.date()
        flatten_time = self.parse_time_today_et(self.config["flatten_time_et"])

        if self.last_flatten_date == today:
            return False

        return now >= flatten_time

    def mark_flattened_today(self):
        self.last_flatten_date = self.now_et().date()

    def is_news_blocked(self):
        if not self.config.get("news_pause_enabled", False):
            return False, None

        now = self.now_et()

        for window in self.config.get("blocked_news_windows", []):
            start = self.parse_time_today_et(window["start_et"])
            end = self.parse_time_today_et(window["end_et"])

            if start <= now <= end:
                return True, window.get("reason", "News pause")

        return False, None

    def get_trade_count(self):
        key = self.today_key()
        return self.trade_count_by_day.get(key, 0)

    def increment_trade_count(self):
        key = self.today_key()
        self.trade_count_by_day[key] = self.trade_count_by_day.get(key, 0) + 1

    def max_trades_reached(self):
        return self.get_trade_count() >= int(self.config["max_trades_per_day"])

    def is_locked_out(self):
        key = self.today_key()
        return self.locked_out_by_day.get(key, False)

    def update_daily_loss_lockout(self, current_balance: float):
        key = self.today_key()

        if key not in self.starting_balance_by_day:
            self.starting_balance_by_day[key] = current_balance
            return False

        starting_balance = self.starting_balance_by_day[key]
        pnl_today = current_balance - starting_balance

        if pnl_today <= -abs(float(self.config["daily_loss_limit"])):
            self.locked_out_by_day[key] = True
            return True

        return False

    def can_take_new_trade(self):
        if self.is_manual_paused():
            return False, "Manual pause is enabled."

        if self.is_locked_out():
            return False, "Daily loss lockout is active."

        if not self.is_inside_trading_hours():
            return False, "Outside allowed trading hours."

        if self.is_after_no_new_trade_cutoff():
            return False, "No-new-trades cutoff reached."

        if self.max_trades_reached():
            return False, "Max trades per day reached."

        news_blocked, news_reason = self.is_news_blocked()

        if news_blocked:
            return False, news_reason

        return True, "Trading allowed."


# ============================================================
# BOT
# ============================================================

def run_bot(config):
    client = TopstepXClient(
        username=config["username"],
        api_key=config["api_key"],
    )

    client.authenticate()

    risk = RiskManager(config)

    contract = client.search_contract(
        symbol=config["symbol"],
        live=config["live"],
    )

    contract_id = contract["id"]
    contract_name = contract.get("name", config["symbol"])
    tick_size = float(contract["tickSize"])

    print("=" * 60)
    print("TopstepX EMA/ATR Evaluation Bot")
    print("=" * 60)
    print(f"Symbol: {config['symbol']}")
    print(f"Contract: {contract_name}")
    print(f"Contract ID: {contract_id}")
    print(f"Tick size: {tick_size}")
    print(f"Evaluation size: {config['evaluation_size']}")
    print(f"Contracts per 50k: {config['contracts_per_50k']}")

    order_size = contract_size_from_eval(
        evaluation_size=config["evaluation_size"],
        contracts_per_50k=config["contracts_per_50k"],
    )

    print(f"Order size: {order_size}")
    print("=" * 60)

    last_processed_bar_time = None

    while True:
        try:
            # ------------------------------------------------
            # Daily balance / loss lockout
            # ------------------------------------------------
            try:
                current_balance = client.get_account_balance(config["account_id"])
                locked_out = risk.update_daily_loss_lockout(current_balance)

                if locked_out:
                    print("Daily loss limit reached. Bot locked out for the day.")
                    time.sleep(30)
                    continue

            except Exception as balance_error:
                print(f"Balance check warning: {balance_error}")
                print("Trading paused until account balance field is verified.")
                time.sleep(30)
                continue

            # ------------------------------------------------
            # End-of-day flatten
            # ------------------------------------------------
            if risk.should_flatten_now():
                position = client.get_open_position_for_contract(
                    account_id=config["account_id"],
                    contract_id=contract_id,
                )

                if position:
                    print(f"Flatten time reached. Closing position: {position}")

                    close_result = client.close_position(
                        account_id=config["account_id"],
                        contract_id=contract_id,
                    )

                    print(f"Flatten result: {close_result}")

                risk.mark_flattened_today()
                time.sleep(10)
                continue

            # ------------------------------------------------
            # Check whether new trades are allowed
            # ------------------------------------------------
            allowed, reason = risk.can_take_new_trade()

            if not allowed:
                print(f"No new trade: {reason}")
                time.sleep(15)
                continue

            # ------------------------------------------------
            # One-position-at-a-time guard
            # ------------------------------------------------
            if config.get("one_trade_at_a_time", True):
                open_position = client.get_open_position_for_contract(
                    account_id=config["account_id"],
                    contract_id=contract_id,
                )

                if open_position:
                    print(f"Position already open. Waiting: {open_position}")
                    time.sleep(10)
                    continue

                has_open_orders = client.has_open_orders_for_contract(
                    account_id=config["account_id"],
                    contract_id=contract_id,
                )

                if has_open_orders:
                    print("Open order already exists for this contract. Waiting.")
                    time.sleep(10)
                    continue

            # ------------------------------------------------
            # Retrieve completed 2-minute bars
            # ------------------------------------------------
            df = client.retrieve_2m_bars(
                contract_id=contract_id,
                live=config["live"],
                limit=300,
            )

            df = add_indicators(
                df=df,
                ema_fast=config["ema_fast"],
                ema_slow=config["ema_slow"],
                atr_length=config["atr_length"],
            )

            completed_bar = df.iloc[-1]
            bar_time = completed_bar["t"]

            # Avoid duplicate processing of the same completed bar
            if last_processed_bar_time == bar_time:
                time.sleep(5)
                continue

            signal = get_signal(df)

            print(
                f"{bar_time} | Close={completed_bar['close']} "
                f"EMA{config['ema_fast']}={completed_bar['ema_fast']:.2f} "
                f"EMA{config['ema_slow']}={completed_bar['ema_slow']:.2f} "
                f"ATR={completed_bar['atr']:.2f} "
                f"Signal={signal}"
            )

            last_processed_bar_time = bar_time

            if signal is None:
                time.sleep(5)
                continue

            # ------------------------------------------------
            # ATR bracket calculation
            # ------------------------------------------------
            atr = float(completed_bar["atr"])

            if math.isnan(atr) or atr <= 0:
                print("ATR not ready. Signal skipped.")
                time.sleep(5)
                continue

            tp_ticks = ticks_from_atr(
                atr=atr,
                tick_size=tick_size,
                multiplier=config["atr_tp_multiplier"],
            )

            sl_ticks = None

            if config["use_stop_loss"]:
                sl_ticks = ticks_from_atr(
                    atr=atr,
                    tick_size=tick_size,
                    multiplier=config["atr_sl_multiplier"],
                )

            side = 0 if signal == "LONG" else 1

            # ------------------------------------------------
            # Place trade
            # ------------------------------------------------
            print(
                f"Placing {signal} order | Size={order_size} "
                f"TP={tp_ticks} ticks SL={sl_ticks}"
            )

            order_result = client.place_market_order(
                account_id=config["account_id"],
                contract_id=contract_id,
                side=side,
                size=order_size,
                tp_ticks=tp_ticks,
                sl_ticks=sl_ticks,
            )

            print(f"Order placed successfully: {order_result}")

            risk.increment_trade_count()

            time.sleep(5)

        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break

        except Exception as error:
            print(f"Bot error: {error}")
            time.sleep(10)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    run_bot(CONFIG)
