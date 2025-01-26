# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# import os
# import openai
# from PyPDF2 import PdfReader

# # Initialize the app
# app = Flask(__name__)
# CORS(app)

# # Set the directory for file uploads
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# # Route for extracting text from PDF
# @app.route("/api/extract", methods=["POST"])
# def extract_text():
#     if "pdf" not in request.files:
#         return jsonify({"error": "No PDF file provided"}), 400

#     pdf_file = request.files["pdf"]
#     api_key = request.form.get("api_key", "").strip()

#     # Save the uploaded PDF file
#     file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(pdf_file.filename))
#     pdf_file.save(file_path)

#     try:
#         # Extract text from the PDF
#         reader = PdfReader(file_path)
#         # extracted_text = "".join([page.extract_text() for page in reader.pages])
#         # Extract text from PDF and return as a list of pages
#         extracted_text = [page.extract_text() for page in reader.pages]

#         # Optionally refine text with LLM
#         if api_key:
#             openai.api_key = api_key
#             response = openai.Completion.create(
#                 model="gpt-3.5-turbo",
#                 prompt=f"Refine and summarize the following text:\n\n{extracted_text}",
#                 max_tokens=1000,
#             )
#             extracted_text = response.choices[0].text.strip()

#         return jsonify({"text": extracted_text})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     finally:
#         # Cleanup the uploaded file
#         os.remove(file_path)

# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import openai
from PyPDF2 import PdfReader

# Initialize the app
app = Flask(__name__)
CORS(app)

# Set the directory for file uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Route for extracting text from PDF
@app.route("/api/extract", methods=["POST"])
def extract_text():
    # Check if the PDF file is part of the request
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    # Retrieve the PDF file and API key from the form
    pdf_file = request.files["pdf"]
    api_key = request.form.get("api_key", "").strip()  # Primary API key
    if not api_key:
        return jsonify({"error": "No API key provided"}), 400

    openai.api_key = api_key  # Set the OpenAI API key

    # Save the uploaded PDF file
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(pdf_file.filename))
    pdf_file.save(file_path)

    try:
        # Extract text from the PDF
        reader = PdfReader(file_path)
        extracted_text = [page.extract_text() for page in reader.pages]

        # Refine text with LLM, if required
        if extracted_text:
            combined_text = "\n".join(extracted_text)
            response = openai.Completion.create(
                model="gpt-3.5-turbo",  # Stable and widely used OpenAI model
                prompt=f"Refine and summarize the following text:\n\n{combined_text}",
                max_tokens=1500,  # Allowing more tokens for larger PDF content
                temperature=0.7,  # Adjusting creativity
            )
            refined_text = response.choices[0].text.strip()
            return jsonify({"text": refined_text})

        return jsonify({"text": "No text extracted from the PDF."}), 200

    except openai.error.AuthenticationError:
        return jsonify({"error": "Invalid OpenAI API key provided."}), 401
    except openai.error.RateLimitError:
        return jsonify({"error": "API rate limit exceeded. Check your plan or try later."}), 429
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup: Delete the uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    app.run(debug=True)