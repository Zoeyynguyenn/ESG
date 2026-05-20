# Create Project Scaffold Contract

`/start create <project-path>` bắt buộc tạo các file sau bằng template trong thư mục này:

- `AGENTS.md` <= `AGENTS.template.md`
- `.workflow/START.md` <= `START.template.md`
- `.workflow/config.yaml` <= `workflow-config.template.yaml`
- `.planning/` directory
- `README.md` starter (nếu chưa có)
- `adapters/<project-slug>.yaml` skeleton ở workflow root

Bất kỳ scaffold nào thiếu `Start Intent` trong `AGENTS.md` được xem là chưa đạt contract.
