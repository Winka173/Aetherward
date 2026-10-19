# QA Matrix

Trạng thái: `NOT_STARTED` / `IMPLEMENTED_UNVERIFIED` (code có, chưa kiểm chứng trong Unity) / `VERIFIED` (có bằng chứng lệnh) / `BLOCKED`.

Mô phỏng (pure C#) được kiểm chứng bằng `dotnet test`; mọi thứ hiển thị trong Unity là tối đa `IMPLEMENTED_UNVERIFIED`.

| Hạng mục | Mô phỏng | Unity | Bằng chứng |
|---|---|---|---|
| Baseline MVP | VERIFIED | IMPLEMENTED_UNVERIFIED | 64/64 test, UnityCheck 0 lỗi |
