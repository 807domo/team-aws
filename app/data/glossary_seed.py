"""
愛媛探索AIクイズ - 用語集シードデータ

用語を追加・編集する場合はこのファイルだけを変更する。
"""

import uuid

from sqlalchemy.orm import Session

from app.data.models import GlossaryTermModel

GLOSSARY_SEED_DATA: list[dict] = [
    # クラウド基礎
    {"category": "クラウド基礎", "sort_order": 0, "term": "クラウドコンピューティング", "description": "インターネット経由でサーバー・ストレージ・データベースなどのITリソースをオンデマンドで利用する形態。自前でインフラを用意する必要がなく、使った分だけ料金を払う従量課金が特徴。"},
    {"category": "クラウド基礎", "sort_order": 1, "term": "オンプレミス", "description": "自社内にサーバーなどのインフラを設置・運用する形態。クラウドと対比して使われる。初期投資が大きいが、自社でフルコントロールできる。"},
    {"category": "クラウド基礎", "sort_order": 2, "term": "スケーラビリティ", "description": "需要に応じてシステムのリソースを柔軟に拡張・縮小できる性質。クラウドの主な利点のひとつ。"},
    {"category": "クラウド基礎", "sort_order": 3, "term": "可用性（Availability）", "description": "システムが正常に稼働し続けられる割合。99.9%（スリーナイン）や99.99%（フォーナイン）などで表現される。"},
    {"category": "クラウド基礎", "sort_order": 4, "term": "オンデバイスAI（エッジAI）","description": "クラウドサーバーではなく、スマホやノートPCなどのローカルデバイス上で直接AIモデルを実行する技術"},
    {"category": "クラウド基礎", "sort_order": 5, "term": "GPU (Graphics Processing Unit)","description": "元々は画像処理用であるが、多数の数学的計算を並列で同時に実行できるため、AIの学習と推論に不可欠なチップ"},
    
    # AWSサービス
    {"category": "AWSサービス", "sort_order": 0, "term": "Amazon S3", "description": "AWSのオブジェクトストレージサービス。画像・動画・バックアップなど任意のファイルを保存できる。容量制限がなく、高い耐久性（イレブンナイン）を持つ。"},
    {"category": "AWSサービス", "sort_order": 1, "term": "Amazon EC2", "description": "AWSの仮想サーバー（インスタンス）サービス。OSやスペックを自由に選んで起動でき、Webサーバーやアプリサーバーとして使われる。"},
    {"category": "AWSサービス", "sort_order": 2, "term": "AWS Lambda", "description": "サーバーを管理せずにコードを実行できるサーバーレスコンピューティングサービス。イベント駆動で動作し、実行時間に応じた課金となる。"},
    {"category": "AWSサービス", "sort_order": 3, "term": "Amazon RDS", "description": "MySQL・PostgreSQL・Auroraなどのリレーショナルデータベースをマネージドで提供するサービス。バックアップやパッチ適用をAWSが代行する。"},
    
    # AI基礎
    {"category": "AI基礎", "sort_order": 0, "term": "機械学習（Machine Learning）", "description": "データからパターンを学習し、予測・分類などを行うAIの手法。明示的なルールをプログラムせず、データから自動的にモデルを構築する。"},
    {"category": "AI基礎", "sort_order": 1, "term": "深層学習（Deep Learning）", "description": "ニューラルネットワークを多層に重ねた機械学習の手法。画像認識・音声認識・自然言語処理などで高い精度を発揮する。"},
    {"category": "AI基礎", "sort_order": 2, "term": "大規模言語モデル（LLM）", "description": "大量のテキストデータで事前学習された言語AIモデル。文章生成・翻訳・要約・質問応答などができる。GPT・Claude・Geminiなどが代表例。"},
    {"category": "AI基礎", "sort_order": 3, "term": "プロンプトエンジニアリング", "description": "AIモデルから望ましい出力を得るために、入力文（プロンプト）を設計・最適化する技術。指示の書き方や例示の方法で出力品質が大きく変わる。"},
    {"category": "AI基礎", "sort_order": 4, "term": "ニューラルネットワーク", "description": "人間の脳の構造をモデルにした計算モデル。層状に重なった「ニューロン」が情報を処理し、複雑なパターンを学習する。"},
    {"category": "AI基礎", "sort_order": 5, "term": "トークン", "description": "AIがテキストを処理する際の最小単位。単語や文字の一部として分割され、モデルはこの単位で計算を行う。"},
    {"category": "AI基礎", "sort_order": 6, "term": "ハルシネーション", "description": "AIが事実に基づかない、または誤った情報を、もっともらしく生成してしまう現象。「幻覚」とも呼ばれる。"},
    {"category": "AI基礎", "sort_order": 7, "term": "AIエージェント", "description": "与えられた目標に対し、自ら計画を立ててツールを使い、自律的にタスクを実行するAIシステムのこと。"},
    {"category": "AI基礎", "sort_order": 8, "term": "RAG（検索拡張生成）", "description": "AIが回答する際、外部の最新データや社内文書などを検索・参照することで、回答の正確性を高める仕組み。"},
    
    # AWS AIサービス
    {"category": "AWS AIサービス", "sort_order": 0, "term": "Amazon Bedrock", "description": "AWSのマネージド生成AIサービス。Claude（Anthropic）・Llama・Titanなど複数のファンデーションモデルをAPIで利用できる。モデルの学習・管理が不要。"},
    {"category": "AWS AIサービス", "sort_order": 1, "term": "Amazon Rekognition", "description": "画像・動画の分析サービス。顔認識・物体検出・テキスト抽出などができる。独自のMLモデルを用意しなくても使える。"},
    {"category": "AWS AIサービス", "sort_order": 2, "term": "Amazon Comprehend", "description": "自然言語処理（NLP）サービス。感情分析・エンティティ抽出・言語検出などをAPIで提供する。カスタム分類モデルの学習も可能。"},
    {"category": "AWS AIサービス", "sort_order": 3, "term": "Amazon SageMaker", "description": "機械学習モデルの構築・学習・デプロイを一貫して行えるMLプラットフォーム。JupyterノートブックからMLOpsまで幅広くカバーする。"},
]


def seed_glossary(db: Session) -> bool:
    """用語集の初期データを投入する。

    既にデータが存在する場合はスキップする。

    Returns:
        True: 投入した場合 / False: スキップした場合
    """
    existing = db.query(GlossaryTermModel).first()
    if existing:
        return False

    for item in GLOSSARY_SEED_DATA:
        term = GlossaryTermModel(
            id=str(uuid.uuid4()),
            category=item["category"],
            sort_order=item["sort_order"],
            term=item["term"],
            description=item["description"],
        )
        db.add(term)

    db.commit()
    return True