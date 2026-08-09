@echo off
chcp 65001 > nul
title Telegram Bot EVN Bill Checker - t.me/check_dien_evn_bot
echo ========================================================
echo   TELEGRAM BOT TRA CUU HOA DON DIEN EVN TOAN QUOC
echo   Bot Username: @check_dien_evn_bot
echo ========================================================
echo.

set TELEGRAM_BOT_TOKEN=8972194053:AAFk83IeojjcLXxUBe_jFJuYO4Lg24rsS-k

echo Dang khoi chay Telegram Bot...
echo.

python -u evn_checker/bot.py %TELEGRAM_BOT_TOKEN%

pause
