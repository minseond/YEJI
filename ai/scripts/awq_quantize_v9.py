# =============================================================
# Colab에서 실행: tellang/yeji-4b-instruct-v9 → AWQ 양자화
# =============================================================
# 런타임: GPU (A100 또는 L4 권장, T4도 가능)
# =============================================================

# --- 1. 설치 ---
# !pip install autoawq transformers accelerate huggingface_hub -q

# --- 2. 로그인 ---
# from huggingface_hub import login
# login()  # HF 토큰 입력

# --- 3. 양자화 실행 ---
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

MODEL_ID = "tellang/yeji-4b-instruct-v9"
OUTPUT_DIR = "yeji-4b-instruct-v9-AWQ"
HF_REPO = "tellang/yeji-4b-instruct-v9-AWQ"

print(f"모델 로딩: {MODEL_ID}")
model = AutoAWQForCausalLM.from_pretrained(MODEL_ID)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

# AWQ 양자화 설정 (v7, v8과 동일)
quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM",
}

print("AWQ 양자화 시작...")
model.quantize(tokenizer, quant_config=quant_config)
print("양자화 완료!")

# --- 4. 저장 ---
print(f"로컬 저장: {OUTPUT_DIR}")
model.save_quantized(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# --- 5. HF 업로드 ---
print(f"HF 업로드: {HF_REPO}")
from huggingface_hub import HfApi
api = HfApi()
api.create_repo(HF_REPO, exist_ok=True)
api.upload_folder(
    folder_path=OUTPUT_DIR,
    repo_id=HF_REPO,
    commit_message="feat: AWQ 4-bit 양자화 (w4, g128, GEMM)",
)
print(f"업로드 완료! https://huggingface.co/{HF_REPO}")
