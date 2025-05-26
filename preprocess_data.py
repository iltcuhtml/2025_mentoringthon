# 필요한 라이브러리 불러오기
import pandas as pd
import re
from konlpy.tag import Okt
import os
import joblib
import uuid

print("--- 데이터 전처리 스크립트 시작 ---")

# --- 함수 정의 (블록 밖에 둡니다) ---

# 2. 커스텀 CSV 라인 파싱 함수 (라벨 인자 추가)
def parse_custom_csv_line(line, label, debug=False): # label 인자 추가
    """
    ID,[Origin]ifg@... 또는 ID,[Origin]... 형식의 CSV 라인에서 메시지 내용을 추출합니다.
    label=1이면 Smishing 형식 (ifg@ 사용), label=0이면 Normal 형식 (콤마 뒤 전체)
    debug=True로 설정 시 파싱 과정 출력
    """
    original_line = line.strip() 
    line = original_line
    
    if not line: 
        if debug: print(f"Debug Parse ({'Smishing' if label==1 else 'Normal'}): 빈 줄")
        return None 

    parts_by_comma = line.split(',', 1)
    if len(parts_by_comma) < 2:
        if debug: print(f"Debug Parse ({'Smishing' if label==1 else 'Normal'}): 콤마 구분 실패 - '{original_line[:50]}...'")
        return None

    # id_part = parts_by_comma[0] 
    rest_part = parts_by_comma[1] 

    raw_message = None # 파싱된 메시지를 저장할 변수

    if label == 1: # Smishing 데이터 형식 (ifg@ 사용)
        parts_by_ifg = rest_part.split('ifg@')
        if len(parts_by_ifg) < 2:
             if debug: print(f"Debug Parse (Smishing): 'ifg@' 구분 실패 - '{original_line[:50]}...'")
             return None
        # ifg@ 뒤의 모든 부분을 합침
        raw_message = ''.join(parts_by_ifg[1:]).strip()
        
    elif label == 0: # Normal 데이터 형식 (콤마 뒤 전체)
        # 콤마 뒤의 나머지 부분을 메시지로 간주
        raw_message = rest_part.strip()
        # 만약 Normal 메시지에서 [Origin] 부분을 제거해야 한다면 여기에 추가 로직 구현
        # 예: raw_message = re.sub(r'^\[.*?\]', '', raw_message).strip() # [Origin] 패턴 제거
        if debug: print(f"Debug Parse (Normal): 콤마 뒤 전체 추출 -> '{raw_message[:50]}...'") # Normal 데이터 파싱 결과 출력
        
    # 메시지 내용이 비어있는지 최종 확인
    if not raw_message:
         if debug: print(f"Debug Parse ({'Smishing' if label==1 else 'Normal'}): 메시지 내용 비어있음")
         return None
    
    # 파싱 성공 시 메시지 내용 일부 출력 (디버그 모드일 때만)
    if debug: print(f"Debug Parse ({'Smishing' if label==1 else 'Normal'}): 파싱 성공 -> '{raw_message[:50]}...'")
    
    return raw_message

# 3. 데이터 불러오기 (커스텀 파싱 적용) 함수 - 라벨을 파싱 함수로 전달
def load_and_parse_single_directory(directory_path, label, encoding='utf-8', debug_parsing=False): # label, debug_parsing 인자 추가
    """
    지정된 *하나의* 폴더에서 CSV 파일을 읽고 커스텀 파싱하여 raw 데이터와 라벨을 추출합니다.
    debug_parsing=True로 설정 시 각 라인 파싱 결과 출력
    """
    all_raw_data = [] 
    all_labels = []   
    
    if not os.path.isdir(directory_path):
        print(f"경고: 폴더 '{directory_path}'가 존재하지 않습니다. 건너뜁니다.")
        return pd.DataFrame()

    all_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.endswith('.csv')]
    
    if not all_files:
        print(f"경고: 폴더 '{directory_path}'에 CSV 파일이 없습니다.")
        return pd.DataFrame()

    print(f"\n>>> 폴더 '{directory_path}' ({'Smishing' if label == 1 else 'Normal'})에서 {len(all_files)}개의 CSV 파일을 찾았습니다. 파싱 시작...")

    current_folder_data_count = 0
    for filename in all_files:
        print(f">>>   파일 '{filename}' 파싱 중...")
        try:
            with open(filename, 'r', encoding=encoding, errors='ignore') as f: 
                for i, line in enumerate(f):
                    # 파싱 함수 호출 시 label 인자 전달
                    raw_message = parse_custom_csv_line(line, label=label, debug=debug_parsing) 
                    if raw_message is not None:
                        all_raw_data.append(raw_message)
                        all_labels.append(label)
                        current_folder_data_count += 1
                    # else: # 파싱 실패 시에도 줄 번호는 출력하도록 (선택 사항)
                        # if debug_parsing: print(f"Debug: 파일 '{filename}' 줄 {i+1}: 파싱 실패")

        except Exception as e:
            print(f"오류: '{filename}' 파일 읽기 중 오류 발생: {e}") # 파싱 함수 내 오류는 parse_custom_csv_line에서 처리

    print(f">>> 폴더 '{directory_path}'에서 총 {current_folder_data_count} 건의 데이터 파싱 완료.") 
    
    df_raw = pd.DataFrame({'raw_text': all_raw_data, 'label': all_labels})
    return df_raw

# 4. 데이터 전처리 함수 (Okt 인스턴스를 인자로 받음)
def preprocess_text_sequential(text, okt_instance):
    """
    텍스트 데이터 전처리 함수 (순차 실행용):
    Okt 객체 인스턴스를 인자로 받습니다.
    """
    korean_stopwords = ['의', '가', '이', '은', '는', '와', '과', '에게', '에게서', '에서', '로', '으로', '와', '으로', '하다', '이다', '되다', '있다', '에게', '입니다', '습니다'] 

    if not isinstance(text, str): 
        return ""

    text = re.sub(r'https?://\S+|www\.\S+', '<URL>', text)
    # 전화번호 정규식 수정 (이전 오타 정규식)
    # text = re.sub(r'(\d{2{,\d+}}[-\.\s]?\d{3,4}[-\.\s]?\d{4})|(tel:\d+)', '<PHONENUM>', text) 
    text = re.sub(r'(\d{2,4}[-\.\s]?\d{3,4}[-\.\s]?\d{4})|(tel:\d+)', '<PHONENUM>', text) # 수정된 정규식 적용
    text = re.sub(r'\d{1,3}(,\d{3})*\s*원|\d+만원', '<AMOUNT>', text)
    text = re.sub(r'\d+', '<NUMBER>', text)
    text = re.sub(r'[^가-힣a-zA-Z<>\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return ""
    tokens = okt_instance.morphs(text, stem=True) 
    tokens = [word for word in tokens if word not in korean_stopwords and (len(word) > 1 or word in ['<URL>', '<PHONENUM>', '<AMOUNT>', '<NUMBER>'])] 

    return ' '.join(tokens)


# --- 메인 실행 로직 시작 ---
if __name__ == "__main__":
    print("--- 메인 실행 로직 시작 ---")

    # --- 설정 (블록 안으로 옮깁니다) ---
    # TODO: 원본 raw CSV 파일들이 있는 폴더 경로를 설정해주세요.
    # [(폴더 경로, 라벨), ...] 형태의 리스트. 라벨은 0 (Normal) 또는 1 (Smishing).
    raw_data_sources = [
        ('csv/normal/1', 0), 
        ('csv/normal/2', 0), 
        ('csv/normal/3', 0), 
        ('csv/normal/4', 0), 
        ('csv/normal/5', 0), 
        ('csv/normal/6', 0), 
        ('csv/normal/7', 0), 
        ('csv/normal/8', 0), 
        ('csv/normal/9', 0),
        ('csv/smishing/1', 1), 
        ('csv/smishing/2', 1), 
        ('csv/smishing/3', 1), 
        ('csv/smishing/4', 1), 
        ('csv/smishing/5', 1), 
        ('csv/smishing/6', 1), 
        ('csv/smishing/7', 1), 
        ('csv/smishing/8', 1), 
        ('csv/smishing/9', 1)
    ] 

    # TODO: 전처리된 데이터 .pkl 파일들을 저장할 *상위* 폴더 경로를 설정해주세요.
    # 이 폴더 안에 각 소스별로 .pkl 파일이 생성됩니다.
    output_processed_data_dir = 'data/processed_data'

    # 파일 인코딩 설정
    file_encoding = 'utf-8'
    # TODO: 디버깅 모드 설정. Normal 데이터 파싱 문제 해결 시 False로 변경
    debug_parsing_mode = True 

    # KoNLPy Okt 객체를 메인 프로세스에서 한 번만 초기화
    try:
         print("KoNLPy Okt 형태소 분석기 로딩 중...")
         okt_processor = Okt()
         print("KoNLPy Okt 로딩 완료.")
    except Exception as e:
         print(f"오류: KoNLPy Okt 초기화 중 오류 발생: {e}")
         print("Konlpy 및 JPype 설치 상태를 확인해주세요.")
         exit()

    # 출력 폴더 생성 (없으면)
    if not os.path.exists(output_processed_data_dir):
        os.makedirs(output_processed_data_dir)
        print(f"출력 폴더 '{output_processed_data_dir}' 생성 완료.")
        
    # --- 각 데이터 소스별로 로드, 파싱, 전처리 및 저장 ---
    print("\n--- 각 데이터 소스별 전처리 및 저장 시작 ---")
    
    total_processed_count = 0
    for source_path, source_label in raw_data_sources:
        # 특정 폴더의 데이터 로드 및 파싱 (라벨과 디버그 모드 전달)
        df_raw_single_source = load_and_parse_single_directory(source_path, source_label, encoding=file_encoding, debug_parsing=debug_parsing_mode)

        if df_raw_single_source.empty:
            print(f"경고: 폴더 '{source_path}'에서 유효한 데이터가 파싱되지 않았습니다. 이 소스는 건너뜁니다.")
            continue

        # 전처리 적용 (순차 처리)
        print(f">>> 폴더 '{source_path}' 데이터 전처리 시작...")
        df_raw_single_source['processed_text'] = df_raw_single_source['raw_text'].apply(
            lambda text: preprocess_text_sequential(text, okt_processor)
        )
        print(f">>> 폴더 '{source_path}' 데이터 전처리 완료. ({len(df_raw_single_source)} 건)")

        # 전처리된 데이터 저장
        folder_name = os.path.basename(source_path)
        output_pkl_filename = f'processed_data_{folder_name}_{source_label}.pkl'
        output_pkl_path = os.path.join(output_processed_data_dir, output_pkl_filename)

        # 필요한 컬럼만 선택하여 저장
        df_to_save = df_raw_single_source[['processed_text', 'label']]

        # pickle 형식으로 저장
        print(f">>> 전처리된 데이터 저장 시작 -> '{output_pkl_path}'")
        try:
            df_to_save.to_pickle(output_pkl_path)
            print(f">>> '{output_pkl_path}'에 성공적으로 저장되었습니다. 데이터 수: {len(df_to_save)}")
            total_processed_count += len(df_to_save)
        except Exception as e:
            print(f"오류: '{output_pkl_path}' 저장 중 오류 발생: {e}")

    print(f"\n--- 모든 데이터 소스 전처리 및 분할 저장 완료. 총 전처리된 데이터 수: {total_processed_count} ---")
    print(f"전처리된 .pkl 파일들은 폴더 '{output_processed_data_dir}'에 저장되었습니다.")
    print("--- 데이터 전처리 스크립트 종료 ---")