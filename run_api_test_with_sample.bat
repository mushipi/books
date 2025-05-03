@echo off
echo ===============================================
echo Gemini API �e�X�g���s�X�N���v�g
echo ===============================================

set TEST_IMAGE="pic\bunkobon-urabyousi_2-1024x683.jpg"

echo �g�p����摜: %TEST_IMAGE%

if not exist venv\Scripts\activate (
    echo ���z����������܂���
    pause
    exit /b
)

call venv\Scripts\activate

echo ===============================================
echo 1. ���݂�API�����i���N�G�X�g���ڑ��M�j�ł̃e�X�g
echo ===============================================
python test_gemini_api_current.py %TEST_IMAGE%

echo ===============================================
echo 2. google-generativeai���C�u�������g�p�����e�X�g
echo ===============================================
echo ���C�u�������C���X�g�[�����Ă��܂�...
pip install google-generativeai -q

python test_gemini_api_new.py %TEST_IMAGE%

echo ===============================================
echo �e�X�g����
echo ===============================================

pause
