import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

USERNAME = "baonguyenn2302"


def main():
    password = getpass.getpass("Đặt mật khẩu đăng nhập: ")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == USERNAME))
        if user is None:
            user = User(username=USERNAME)
            db.add(user)

        user.password = hash_password(password)
        user.full_name = "Nguyễn Gia Bảo"
        user.student_id = "B23DCCN075"
        user.class_name = "D23CNPM03"
        user.faculty = "Information Technology 1"
        user.email = "baonguyenn.contact@gmail.com"
        user.phone = "0912825535"
        user.links = {
            "github": "https://github.com/baonguyenn2302/IoT_smart_house",
            "figma": "https://www.figma.com/design/QK22BD6yGsamUvZu4HptgJ/IoT?node-id=0-1&t=PLOkjpVU0f5y2w0h-1",
            "report_pdf": "/srs.pdf",
        }
        db.commit()
        print("Đã tạo hoặc cập nhật user", USERNAME)


if __name__ == "__main__":
    main()