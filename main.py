import argparse
import json
import logging
import logging.handlers as handlers
import random
import sys
import os
from pathlib import Path

from src import (
    Browser,
    DailySet,
    GamingTab,
    Login,
    MorePromotions,
    PunchCards,
    Searches,
)
from src.constants import VERSION
from src.loggingColoredFormatter import ColoredFormatter
from src.notifier import Notifier

POINTS_COUNTER = 0


def main():
    setup_logging()
    args = argument_parser()
    notifier = Notifier(args)
    setup_logging(args.verbosenotifs, notifier)
    loaded_accounts = setup_accounts()
    for current_account in loaded_accounts:
        try:
            execute_bot(current_account, notifier, args)
        except Exception as e:
            logging.exception(f"{e.__class__.__name__}: {e}")


def setup_logging(verbose_notifs=False, notifier=None):
    ColoredFormatter.verbose_notifs = verbose_notifs
    ColoredFormatter.notifier = notifier

    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "logs"))
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                os.path.join(log_dir, "activity.log"),
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )


def argument_parser():
    parser = argparse.ArgumentParser(description="Microsoft Rewards Farmer")
    parser.add_argument(
        "-v", "--visible", action="store_true", help="Optional: Visible browser"
    )
    parser.add_argument(
        "-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)"
    )
    parser.add_argument(
        "-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-t",
        "--telegram",
        metavar=("TOKEN", "CHAT_ID"),
        nargs=2,
        type=str,
        default=None,
        help="Optional: Telegram Bot Token and Chat ID (ex: 123456789:ABCdefGhIjKlmNoPQRsTUVwxyZ 123456789)",
    )
    parser.add_argument(
        "-d",
        "--discord",
        type=str,
        default=None,
        help="Optional: Discord Webhook URL (ex: https://discord.com/api/webhooks/123456789/ABCdefGhIjKlmNoPQRsTUVwxyZ)",
    )
    parser.add_argument(
        "-vn",
        "--verbosenotifs",
        action="store_true",
        help="Optional: Send all the logs to discord/telegram",
    )
    parser.add_argument(
        "--currency",
        help="Converts your points into your preferred currency.",
        choices=["EUR", "USD", "AUD", "INR", "GBP", "CAD", "JPY",
                 "CHF", "NZD", "ZAR", "BRL", "CNY", "HKD", "SGD", "THB"],
        action="store",
        required=False,
    )
    return parser.parse_args()


def banner_display():
    farmer_banner = """
    ███╗   ███╗███████╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗
    ████╗ ████║██╔════╝    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██╔████╔██║███████╗    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝
    ██║╚██╔╝██║╚════██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║███████║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║
    ╚═╝     ╚═╝╚══════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝"""
    logging.error(farmer_banner)
    logging.warning(
        f"        by Charles Bel (@charlesbel)               version {VERSION}\n"
    )


def setup_accounts():
    account_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "accounts.json"))
    if not os.path.exists(account_path):
        with open(account_path, "w", encoding="utf-8") as account_file:
            account_file.write(
                json.dumps(
                    [{"username": "Your Email", "password": "Your Password"}], indent=4
                )
            )
        no_accounts_notice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(no_accounts_notice)
        sys.exit()

    with open(account_path, "r", encoding="utf-8") as account_file:
        loaded_accounts = json.load(account_file)
    random.shuffle(loaded_accounts)
    return loaded_accounts


def execute_bot(current_account, notifier, args):
    logging.info(
        f'********************{current_account.get("username", "")}********************'
    )
    with Browser(mobile=False, account=current_account, args=args) as desktop_browser:
        account_points_counter = Login(desktop_browser).login()
        starting_points = account_points_counter
        logging.info(
            f"[POINTS] You have {desktop_browser.utils.formatNumber(account_points_counter)} points on your account !"
        )
        GamingTab(desktop_browser).completeGamingTab()
        DailySet(desktop_browser).completeDailySet()
        PunchCards(desktop_browser).completePunchCards()
        MorePromotions(desktop_browser).completeMorePromotions()
        (
            remaining_searches,
            remaining_searches_m,
        ) = desktop_browser.utils.getRemainingSearches()
        if remaining_searches != 0:
            account_points_counter = Searches(desktop_browser).bingSearches(
                remaining_searches
            )

        if remaining_searches_m != 0:
            desktop_browser.closeBrowser()
            with Browser(
                mobile=True, account=current_account, args=args
            ) as mobile_browser:
                account_points_counter = Login(mobile_browser).login()
                account_points_counter = Searches(mobile_browser).bingSearches(
                    remaining_searches_m
                )
        desktop_browser.closeBrowser()

        total_earned = account_points_counter - starting_points
        total_overall = account_points_counter

        message = (
            f"[POINTS] You have earned {desktop_browser.utils.formatNumber(total_earned)} points today !\n"
            f"[POINTS] You are now at {desktop_browser.utils.formatNumber(total_overall)} points !\n"
        )

        if args.currency:
            message += f"💵 Total earned points: {total_earned} " \
                       f"({format_currency(total_earned, args.currency)}) \n"
            message += f"💵 Total Overall points: {total_overall} " \
                       f"({format_currency(total_overall, args.currency)})"

        logging.info(message)

        notifier.send(
            "\n".join(
                [
                    "Microsoft Rewards Farmer",
                    f"Account: {current_account.get('username', '')}",
                    f"⭐️ Points earned today: {desktop_browser.utils.formatNumber(total_earned)}",
                    f"🏅 Total points: {desktop_browser.utils.formatNumber(total_overall)}",
                ]
            )
        )


def format_currency(points, currency):
    convert = {
        "EUR": {"rate": 1500, "symbol": "€"},
        "AUD": {"rate": 1350, "symbol": "AU$"},
        "INR": {"rate": 16, "symbol": "₹"},
        "USD": {"rate": 1300, "symbol": "$"},
        "GBP": {"rate": 1700, "symbol": "£"},
        "CAD": {"rate": 1000, "symbol": "CA$"},
        "JPY": {"rate": 12, "symbol": "¥"},
        "CHF": {"rate": 1400, "symbol": "CHF"},
        "NZD": {"rate": 1200, "symbol": "NZ$"},
        "ZAR": {"rate": 90, "symbol": "R"},
        "BRL": {"rate": 250, "symbol": "R$"},
        "CNY": {"rate": 200, "symbol": "¥"},
        "HKD": {"rate": 170, "symbol": "HK$"},
        "SGD": {"rate": 950, "symbol": "S$"},
        "THB": {"rate": 40, "symbol": "฿"}
    }
    return f"{convert[currency]['symbol']}{points / convert[currency]['rate']:0.02f}"


if __name__ == "__main__":
    banner_display()
    main()
