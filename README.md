# DeltaSupport

Desktop app nội bộ cho Delta Assistant, viết bằng `CustomTkinter`, dùng backend `FastAPI` + `SQL Server`.

README này được viết để:
- giúp người mới hoặc AI khác hiểu project nhanh
- chỉ rõ frontend/backend đang nằm ở đâu
- ghi lại các luồng chính, quyền, và các điểm dễ vấp

## Rất Quan Trọng Cho AI Khác

Đây là phần bắt buộc phải đọc trước khi sửa gì trong project này.

### 1. Chủ project không biết code

Người đang trực tiếp build app này là chủ project, nhưng:
- gần như không có nền tảng code
- đang vừa làm vừa học
- cần được giải thích chậm, rõ, từng bước
- cần hướng dẫn theo kiểu thực hành, không dùng quá nhiều thuật ngữ nếu không giải thích

Vì vậy khi hỗ trợ:
- không giả định user hiểu Git, cloud, deploy, API, schema, SQL migration
- không đưa hướng dẫn kiểu nhảy bước
- nếu cần thao tác nhiều bước, hãy viết theo thứ tự rất rõ ràng
- ưu tiên nói theo kiểu: “bước 1 làm gì, bước 2 làm gì, nếu lỗi thì xem gì”

### 2. Project đang tách 2 máy

Hiện tại project được chia làm 2 nơi:

- Máy dev:
  - là máy user đang mở IDE và chat với AI
  - có frontend app
  - có thêm bản copy backend để đọc/sửa/debug
- Máy chủ:
  - là nơi backend thật đang chạy
  - dùng SQL Server thật
  - app frontend ngoài thực tế đang gọi tới backend ở máy này

Điều này có nghĩa:
- sửa backend trong workspace hiện tại không tự cập nhật máy chủ
- sau khi sửa backend ở máy dev, cần copy file đã sửa sang máy chủ
- rồi restart backend trên máy chủ thì thay đổi mới có hiệu lực thật

AI khác phải luôn nhớ:
- hỏi/thông báo rõ phần nào chỉ đang sửa ở bản copy
- nếu user nói “đã sửa rồi mà app không đổi”, phải kiểm tra xem user đã copy file lên máy chủ và restart backend chưa

### 3. Cách hỗ trợ phù hợp với user này

Khi hướng dẫn, ưu tiên:
- ngắn gọn nhưng không nhảy bước
- dùng ngôn ngữ dễ hiểu
- giải thích thêm “vì sao làm bước này” nếu bước đó dễ gây hoang mang
- nếu có nhiều lựa chọn, đưa ra lựa chọn dễ nhất trước

Không nên:
- ném ra quá nhiều phương án cùng lúc
- giả định user biết dùng terminal thành thạo
- yêu cầu user tự suy luận các bước deploy

### 4. Những phần user đã chốt giữ nguyên

Nếu user đã nói rõ một phần:
- “đừng đổi UI”
- “mình đang ưng phần này rồi”
- “chỉ sửa đúng chỗ mình nói”

thì phải coi đó là ràng buộc cứng.

AI khác không được:
- tự tiện redesign lại phần đó
- “tiện tay” refactor hoặc đổi layout nếu user không yêu cầu
- sửa lan sang các phần user đã chốt giữ nguyên

Đặc biệt trong project này:
- user rất quan tâm cảm giác UI
- có những phần user đã ưng và muốn giữ nguyên hoàn toàn
- nếu cần sửa gần khu vực đó, chỉ chạm đúng phạm vi được yêu cầu

### 4.1. Các rule UI đã chốt cứng

Từ thời điểm này, AI/dev sau không được tự ý "tinh chỉnh thêm" các phần dưới đây nếu user không yêu cầu trực tiếp.

- Chỉ có 2 trạng thái cửa sổ:
  - `windowed`
  - `maximized`
- Nút maximize của Windows phải bấm được bình thường.
- Không được thêm kiểu resize tự do, scale tự do, hay responsive ngoài ý user.
- Ở `windowed`, layout phải giữ đúng tỷ lệ đã chốt, không tự co giãn linh tinh.
- Header/topbar phải ưu tiên giữ bố cục cố định, không tự wrap thành nhiều hàng nếu user không yêu cầu.
- Cụm bên phải của topbar phải là một khối sát nhau:
  - `clock`
  - cột thông tin `Delta Assistant / Version / User`
  - nút `Setting`
  - nút `Log out`
- Khoảng cách giữa 4 phần trên phải rất sát nhau, chỉ chừa khoảng nhỏ, không để khoảng hở lớn.
- Cột thông tin bên phải phải căn giữa cho đều mắt.
- Text version hiện tại phải là:
  - `Version: 0.0.1`
- Không được tự ý đổi lại `Ver 0.0.1`.

### 4.2. Landing screen sau login đã chốt

- Sau khi login thành công, màn đầu tiên là màn hình chào mừng.
- Nội dung gồm:
  - `logo.png`
  - dòng `Welcome to Delta Support`
  - dòng `A product within the All In One Merchant ecosystem.`
  - nút `Start`
- Chỉ sau khi bấm `Start` mới hiện các function/menu để chọn.
- Đây là flow đã chốt, không tự ý bỏ hoặc redesign lại nếu user không yêu cầu.

### 4.3. Rule hiển thị menu theo department/role đã chốt

- UI hiện tại đang là UI của `Technical Support`.
- Các phòng ban khác sẽ có giao diện/menu riêng về sau.
- `Work Schedule` là menu dùng chung cho mọi phòng ban, mọi nhân viên đều thấy.
- Các function kỹ thuật như:
  - `POS`
  - `SQL`
  - `Link / Data`
  - `Cách xử lý`
  chỉ dành cho `Technical Support`.
- `SQL` không hiển thị cho:
  - `TS Junior`
  - `TS Probation`
- `SQL` chỉ hiển thị cho:
  - `TS Senior`
  - `TS Leader`
  - và các role quản trị nếu đang được cấp quyền trong code

### 4.4. Rule PIN/OTP đã chốt

- Nếu người dùng quên PIN, phải có nút `Forgot`.
- Flow chuẩn:
  1. bấm `Forgot`
  2. gửi OTP về email đã đăng ký
  3. chỉ hiện thông báo tiếng Anh rằng OTP đã gửi tới email đã đăng ký
  4. không được hiện nguyên email trên UI
  5. nhập OTP đúng thì được đặt PIN mới
- OTP là `6 digits`.
- PIN luôn là `4 digits`.
- Không được để lẫn logic giữa OTP 6 số và PIN 4 số.

### 4.5. Từ đây ưu tiên phát triển function, không tiếp tục sửa UI nếu không được yêu cầu

- User đã yêu cầu rõ: từ đây tập trung phát triển function.
- AI/dev sau không được tiếp tục “tiện tay” sửa:
  - topbar
  - spacing
  - window mode
  - landing screen
  - căn chỉnh các cụm đã chốt
- Chỉ sửa UI nữa nếu user chỉ đích danh phần cần sửa.

### 5. Luôn cập nhật tiến trình

AI khác nên luôn nói rõ:
- đã làm gì
- chưa làm gì
- phần nào đang là workaround/local only
- phần nào muốn chạy thật thì còn phải copy lên máy chủ

Nếu có thay đổi backend:
- phải nói rõ file nào cần copy sang máy chủ
- phải nói rõ có cần restart backend không

### 6. Nguyên tắc giao tiếp

AI khác nên:
- kiên nhẫn
- không dùng giọng dạy đời
- không trả lời kiểu “việc này đơn giản”
- luôn coi mục tiêu là giúp user làm được việc, không phải chứng minh kiến thức

Tone phù hợp:
- chậm rãi
- cụ thể
- hỗ trợ từng bước
- nhắc lại bối cảnh 2 máy khi cần

## Tổng Quan

Project hiện có 2 phần trong cùng workspace:
- `frontend desktop app`: chạy bằng `main.py`
- `backend API`: nằm trong thư mục `backend_server/`

Luồng tổng quát:
1. App mở `SplashScreen`
2. Sang `LoginPage`
3. Login gọi API `/login`
4. Vào `MainAppPage`
5. Các màn hình như `Work Schedule`, `Leave Summary`, `Admin Manager` tiếp tục gọi API backend

## Cấu Trúc Chính

Root:
- [main.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/main.py:1): entry point của app desktop
- [main_app.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/main_app.py:1): layout chính sau login, topbar, navigation, show page
- [splash_screen.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/splash_screen.py:1): màn splash
- [requirements.txt](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/requirements.txt:1): dependency Python

Frontend pages:
- [pages/login_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/login_page.py:1): login UI
- [pages/tech_schedule_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/tech_schedule_page.py:1): lịch làm việc theo tuần
- [pages/leave_summary_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/leave_summary_page.py:1): tổng hợp nghỉ theo tháng
- [pages/leave_request_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/leave_request_page.py:1): tạo request nghỉ
- [pages/admin_approval_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/admin_approval_page.py:1): admin manager
- [pages/schedule_setup_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/schedule_setup_page.py:1): cấu hình nội bộ cho tên hiển thị và lịch cố định

Frontend services:
- [services/auth_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/auth_service.py:1): call API login / pin / schedule
- [services/signup_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/signup_service.py:1): call API sign up
- [services/schedule_config_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/schedule_config_service.py:1): lưu config nội bộ cho `Schedule Setup`

Backend:
- [backend_server/api_server.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/api_server.py:1): FastAPI app
- [backend_server/database.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/database.py:1): kết nối SQL Server
- [backend_server/models.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/models.py:1): request models
- [backend_server/routers/auth.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/auth.py:1): login / change password / register
- [backend_server/routers/admin.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/admin.py:1): admin user management
- [backend_server/routers/pin.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/pin.py:1): PIN flow
- [backend_server/routers/work_schedule.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/work_schedule.py:1): work schedule APIs

## Công Nghệ

Frontend:
- Python
- CustomTkinter
- requests
- Pillow

Backend:
- FastAPI
- Uvicorn
- pyodbc
- SQL Server

## Cách Chạy

### Chạy frontend

Từ root project:

```powershell
python main.py
```

### Chạy backend local

Từ thư mục `backend_server`:

```powershell
uvicorn api_server:app --reload
```

Hoặc nếu cần host/port rõ:

```powershell
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

## Cấu Hình API

Frontend hiện đang gọi tới:
- `https://underline-steersman-crepe.ngrok-free.dev`

Các file đang giữ `API_BASE_URL`:
- [services/auth_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/auth_service.py:1)
- [services/signup_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/signup_service.py:1)
- [services/login_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/login_service.py:1)
- [services/user_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/user_service.py:1)
- [backend_server/routers/admin.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/admin.py:1) không giữ base url nhưng là route backend liên quan

Lưu ý:
- frontend và backend thật đang có thể nằm ở 2 máy khác nhau
- workspace này hiện chứa cả app và bản copy backend để dev/debug
- sửa backend ở đây không tự đẩy lên máy chủ thật

## Database

Kết nối DB đang hard-code tại:
- [backend_server/database.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/database.py:1)

Thông tin hiện tại:
- `SERVER = "localhost"`
- `DATABASE = "DeltaSupport"`
- `USERNAME = "delta_user"`

Nếu deploy thật khác máy:
- cần sửa file này trên máy chủ hoặc đổi sang biến môi trường sau

## Luồng Đăng Nhập

Frontend:
- [pages/login_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/login_page.py:1)

Backend:
- [backend_server/routers/auth.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/auth.py:1)

`/login` hiện trả:
- `username`
- `full_name`
- `role`
- `department`
- `team`

Lưu ý quan trọng:
- trước đây app bị lỗi vì login không giữ đủ `department/team`
- hiện frontend đã giữ lại các field này để quyền trong schedule hoạt động đúng

## Work Schedule

Frontend page:
- [pages/tech_schedule_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/tech_schedule_page.py:1)

Backend routes:
- [backend_server/routers/work_schedule.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/work_schedule.py:1)

API chính:
- `GET /tech-schedule`
- `POST /tech-schedule/update`
- `POST /tech-schedule/update-batch`
- `GET /tech-schedule/month-summary`

### Cách dữ liệu tuần được tạo

Nếu tuần chưa có record trong `dbo.TechSchedule`:
- backend lấy dữ liệu từ `dbo.TechScheduleTemplate`
- rồi sinh record cho 7 ngày của tuần đó

### Quyền sửa lịch

Frontend và backend đều đang áp quyền:
- toàn quyền:
  - `Admin`
  - `Management`
  - `HR`
  - `Accountant`
  - `Leader`
  - `Manager`
- leader theo bộ phận:
  - `TS Leader`
  - `Sale Leader`
  - `MT Leader`
  - `CS Leader`

Rule:
- leader bộ phận chỉ được sửa trong đúng `department`
- riêng `Sale Team` còn phải đúng `team`

### UI hiện tại của schedule

Đã có các cải tiến:
- top bar, nút, logo, dropdown được làm lại cho gọn hơn
- shift header đã đổi từ thanh fill kín sang `badge + accent line`
- text `Shift 1/2/3` hiện căn giữa
- popup đổi status có hiển thị tên tốt hơn

## Leave Summary

Frontend:
- [pages/leave_summary_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/leave_summary_page.py:1)

Backend:
- [backend_server/routers/work_schedule.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/work_schedule.py:224)

Lưu ý:
- route `month-summary` đã được sửa để join `Users` và trả thêm `department/full_name/team`
- frontend có fallback nếu `department` bị rỗng để tránh lọc sạch dữ liệu

## Schedule Setup

Trang mới:
- [pages/schedule_setup_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/schedule_setup_page.py:1)

Dữ liệu local:
- [services/schedule_config_service.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/services/schedule_config_service.py:1)
- file JSON: `data/schedule_config.json`

Mục đích:
- lưu `display_name` có dấu
- lưu `department`, `team`, `shift`
- lưu `VN Time`, `US Time`
- lưu `2 ngày off cố định`

Lưu ý rất quan trọng:
- đây hiện là config nội bộ ở phía app
- chưa đồng bộ xuống SQL server / backend thật
- dùng tốt cho hiển thị tên có dấu và setup nội bộ

## Admin Manager

Main page:
- [pages/admin_approval_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/admin_approval_page.py:1)

Chức năng:
- search user
- filter status / role
- approve
- block / unblock
- edit user
- view audit log

## Những Bẫy Dễ Gặp

### 1. Backend sửa ở đây không tự lên máy chủ

Workspace này chứa bản copy backend để dev.

Sau khi sửa backend:
1. copy file đã sửa lên máy chủ thật
2. chép đè file cũ
3. restart uvicorn / API service

### 2. Schema DB có thể chưa có cột `Users.Team`

Code backend hiện đã có fallback:
- nếu DB chưa có cột `Team`, backend sẽ dùng `General`

Điểm này nằm ở:
- [backend_server/routers/auth.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/auth.py:1)
- [backend_server/routers/work_schedule.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/work_schedule.py:1)

### 3. Nếu bấm Load mà không thấy gì

Checklist:
1. backend có đang chạy không
2. `API_BASE_URL` có đúng không
3. DB có dữ liệu `TechScheduleTemplate` không
4. response API có `success: true` nhưng bị frontend lọc sạch vì `department/team` không khớp không
5. terminal backend trên server có log lỗi SQL không

### 4. Encoding tiếng Việt

Project từng có nhiều chuỗi bị lỗi encoding kiểu:
- `KhÃ´ng`
- `Quyá»n`

Khi sửa thêm text:
- ưu tiên lưu file UTF-8
- kiểm tra lại string sau khi patch

## Các File Thường Phải Copy Lên Máy Chủ

Khi sửa backend schedule/login gần đây, thường phải copy:
- `backend_server/routers/auth.py`
- `backend_server/routers/work_schedule.py`

Sau đó restart backend.

## Gợi Ý Cho AI/Dev Tiếp Theo

Nếu cần hiểu project nhanh, đọc theo thứ tự:
1. [main.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/main.py:1)
2. [main_app.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/main_app.py:1)
3. [pages/login_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/login_page.py:1)
4. [pages/tech_schedule_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/tech_schedule_page.py:1)
5. [backend_server/routers/auth.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/auth.py:1)
6. [backend_server/routers/work_schedule.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/backend_server/routers/work_schedule.py:1)
7. [pages/admin_approval_page.py](/abs/path/c:/Users/AIO%20Tech/Desktop/DeltaSupport/pages/admin_approval_page.py:1)

Nếu cần debug schedule:
- xem frontend filter ở `tech_schedule_page.py`
- xem backend data shape ở `work_schedule.py`
- xem DB schema `Users` có cột `Team` chưa
- xem `TechScheduleTemplate` có dữ liệu không

## Việc Nên Làm Tiếp

- chuyển DB config sang `.env`
- gom `API_BASE_URL` về một chỗ
- chuẩn hóa encoding tiếng Việt
- đồng bộ `Schedule Setup` xuống backend/SQL nếu muốn dùng thật đa máy
- thêm logging rõ hơn ở frontend khi API trả `success=true` nhưng `data=[]`

## Tiến Độ Hiện Tại

### Đã làm

- sửa luồng login để giữ `department/team` ở frontend
- cải thiện topbar:
  - logo
  - nút `Setting`
  - nút `Log out`
  - click logo để về `Home`
- tinh lại dropdown/menu nổi để nhìn “đóng khung” hơn
- tinh lại UI phần shift header trong schedule
- căn giữa chữ `Shift 1/2/3`
- thêm `Schedule Setup` để lưu cấu hình nội bộ:
  - tên hiển thị
  - shift
  - thời gian làm
  - 2 ngày off cố định
- backend login trả thêm `team`
- backend schedule trả thêm:
  - `full_name`
  - `department`
  - `team`
- backend siết quyền sửa schedule theo `department/team`
- backend có fallback nếu DB chưa có cột `Users.Team`
- leave summary backend đã join `Users`
- đã tạo README này để AI/dev sau vào hiểu nhanh

### Đã làm nhưng hiện vẫn là local / nội bộ

- `Schedule Setup` hiện mới là config local trong app
- dữ liệu ở `data/schedule_config.json`
- chưa sync xuống backend/SQL server
- nếu chạy đa máy thì dữ liệu này chưa tự đồng bộ

### Chưa làm

- migrate chính thức DB để đảm bảo `Users.Team` tồn tại ở mọi môi trường
- đồng bộ `Schedule Setup` từ local app xuống backend thật
- làm route backend để tạo/cập nhật template lịch cố định từ UI
- gom cấu hình API/DB sang `.env`
- dọn triệt để lỗi encoding tiếng Việt cũ trong toàn project
- thêm log frontend/backend rõ hơn cho các case “bấm mà trống”

### Nên làm tiếp theo

1. Chuẩn hóa DB server:
   thêm hoặc xác nhận cột `Users.Team`
2. Thêm API backend cho `Schedule Setup`
   để lưu mẫu lịch cố định thật xuống SQL
3. Cho `TechScheduleTemplate` quản lý từ UI thay vì sửa tay trong DB
4. Chuẩn hóa config:
   đưa `API_BASE_URL`, `SERVER`, `DATABASE`, `USERNAME`, `PASSWORD` sang `.env`
5. Dọn encoding tiếng Việt trong cả frontend lẫn backend
