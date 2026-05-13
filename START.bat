@echo off
chcp 65001 >nul
title Khởi động Hệ thống RFM
echo ===================================================
echo   ĐANG KHỞI ĐỘNG HỆ THỐNG PHÂN TÍCH DỮ LIỆU RFM
echo ===================================================
echo.
echo 1. Đang kiểm tra và cài đặt thư viện cần thiết...
python -m pip install -r requirements.txt

echo 2. Đang khởi động Backend server...
start /b python app.py

echo 3. Vui lòng chờ 3 giây để server thiết lập...
timeout /t 3 /nobreak >nul

echo 4. Mở trình duyệt web...
start http://localhost:5000

echo.
echo XONG! Hệ thống đang chạy trên trình duyệt.
echo Vui lòng không đóng cửa sổ đen này trong quá trình sử dụng.
echo Nếu muốn tắt hệ thống, hãy đóng cửa sổ này lại.
echo.
pause
