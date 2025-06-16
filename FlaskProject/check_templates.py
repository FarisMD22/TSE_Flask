import os


def check_templates():
    print("🔍 Checking template structure...")

    # Check if we're in the right directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")

    # Check if templates folder exists
    templates_dir = "templates"
    if os.path.exists(templates_dir):
        print(f"✅ {templates_dir}/ exists")

        # List all files in templates
        for root,dirs,files in os.walk(templates_dir):
            level = root.replace(templates_dir,'').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}📁 {os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}📄 {file}")
    else:
        print(f"❌ {templates_dir}/ does not exist!")
        print("💡 Create it with: mkdir -p templates/students")

    # Check specific student templates
    student_templates = [
        'templates/students/list.html',
        'templates/students/add.html',
        'templates/students/edit.html',
        'templates/students/view.html'
    ]

    print("\n🎯 Checking required student templates:")
    for template in student_templates:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print(f"✅ {template} ({size} bytes)")
        else:
            print(f"❌ {template} - MISSING!")


if __name__ == "__main__":
    check_templates()