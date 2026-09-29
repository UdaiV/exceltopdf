from flask import Flask, request, send_file
import os
from werkzeug.utils import secure_filename
import subprocess
import platform
import zipfile
import uuid
import shutil
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER='output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def get_libreoffice_path():
    # Check common Windows path first if running on Windows
    if platform.system() == 'Windows':
        win_path = r'C:\Program Files\LibreOffice\program\soffice.exe'
        if os.path.exists(win_path):
            return win_path
        # Fallback to Program Files (x86) just in case
        win_path_x86 = r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'
        if os.path.exists(win_path_x86):
            return win_path_x86
    if shutil.which("soffice"):
        return "soffice"
    if shutil.which("libreoffice"):
        return "libreoffice" 
    raise Exception("LibreOffice not found")
    

def render_original_html(download_file=None, error_message=None):
    template_path = os.path.join('templates', 'xltopdf.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    dynamic_html = ""
    if download_file:
        dynamic_html += f'''
          <div style="margin-top: 20px;">
            <a href="/download/{download_file}" style="background-color: green; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">Download Converted PDF</a>
          </div>
        '''
    if error_message:
        dynamic_html += f'''
          <div style="margin-top: 20px; background-color: #ffcccc; padding: 10px; border-radius: 4px; font-weight: bold; color: #990000;">
            Error: {error_message}
          </div>
        '''
        
    if dynamic_html:
        last_div_idx = html_content.rfind('</div>')
        if last_div_idx != -1:
            html_content = html_content[:last_div_idx] + dynamic_html + html_content[last_div_idx:]
            
    return html_content

@app.route('/')
def home():
    return render_original_html()

@app.route('/convert', methods=['POST'])
def convert():
    files=request.files.getlist("files")
    if not files:
        return render_original_html(error_message="No files Selected")
    
    session_id = str(uuid.uuid4())

    upload_dir = os.path.join(
        UPLOAD_FOLDER,
        session_id
    )

    output_dir = os.path.join(
        OUTPUT_FOLDER,
        session_id
    )

    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    try:

        libreoffice = get_libreoffice_path()

        pdf_files = []

        for file in files:

            if file.filename == "":
                continue

            filename = secure_filename(
                file.filename
            )

            if not filename.lower().endswith(
                (".xlsx", ".xls", ".xlsm")
            ):
                continue

            input_path = os.path.join(
                upload_dir,
                filename
            )

            file.save(input_path)

            cmd = [
                libreoffice,
                "--headless",
                "--convert-to",
                "pdf",
                input_path,
                "--outdir",
                output_dir
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(result.stderr)
                continue

            pdf_name = (
                os.path.splitext(filename)[0]
                + ".pdf"
            )

            pdf_path = os.path.join(
                output_dir,
                pdf_name
            )

            if os.path.exists(pdf_path):
                pdf_files.append(pdf_path)

        if not pdf_files:
            return render_original_html(
                error_message="No PDFs generated"
            )

        zip_filename = (
            f"converted_{session_id}.zip"
        )

        zip_path = os.path.join(
            OUTPUT_FOLDER,
            zip_filename
        )

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            for pdf in pdf_files:

                zipf.write(
                    pdf,
                    os.path.basename(pdf)
                )

        return render_original_html(
            download_file=zip_filename
        )

    except Exception as e:

        print(str(e))

        return render_original_html(
            error_message=str(e)
        )



@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    if not os.path.exists(file_path):
        return "File not found", 404

    return send_file(
        file_path,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000))
