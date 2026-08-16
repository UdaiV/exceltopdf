from flask import Flask, request, send_file
import os
import subprocess
import platform

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    return 'libreoffice'  # Linux/Mac default command

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
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            try:
                input_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(input_path)
                
                abs_input_path = os.path.abspath(input_path)
                abs_output_dir = os.path.abspath(UPLOAD_FOLDER)
                
                # Get the correct executable path for the OS
                lo_executable = get_libreoffice_path()
                
                cmd = [lo_executable, '--headless', '--convert-to', 'pdf', '--outdir', abs_output_dir, abs_input_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(result.stderr or "LibreOffice conversion process returned an error.")
                
                base_name, _ = os.path.splitext(file.filename)
                output_pdf_name = f"{base_name}.pdf"
                
                return render_original_html(download_file=output_pdf_name)
            except Exception as e:
                print("Error during conversion:", str(e))
                return render_original_html(error_message=str(e))
                
    return home()

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
