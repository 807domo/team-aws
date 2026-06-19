"""
愛媛探索AIクイズ - シードデータ

初期問題データ（30問以上）を定義し、データベースに投入する。
3コース以上（中予・南予・東予）に分配し、各問題にexam_domainを付与。

CCP ドメイン:
  - Cloud Concepts
  - Security and Compliance
  - Cloud Technology and Services
  - Billing Pricing and Support

AI ドメイン:
  - AI and ML Fundamentals
  - Generative AI
  - Responsible AI
"""

from sqlalchemy.orm import Session

from app.data.models import CourseModel, QuestionModel


# =============================================================================
# コース定義（4コース: 中予・南予・東予 + 追加）
# =============================================================================

COURSES = [
    {
        "id": "matsuyama-basic",
        "name": "松山城コース（基礎）",
        "region": "中予",
        "difficulty": "基礎",
        "description": "松山の名所を巡りながらクラウドの基礎を学ぶ入門コース",
    },
    {
        "id": "uwajima-intermediate",
        "name": "宇和島コース（中級）",
        "region": "南予",
        "difficulty": "中級",
        "description": "宇和島の文化と共にセキュリティ・コスト管理を学ぶ中級コース",
    },
    {
        "id": "shimanami-advanced",
        "name": "しまなみ海道コース（上級）",
        "region": "東予",
        "difficulty": "上級",
        "description": "しまなみ海道を渡りながらAI/MLの応用を学ぶ上級コース",
    },
    {
        "id": "dogo-ai-basic",
        "name": "道後温泉AIコース（基礎）",
        "region": "中予",
        "difficulty": "基礎",
        "description": "道後温泉の歴史と共にAIの基礎概念を学ぶコース",
    },
]


# =============================================================================
# 問題データ（33問: 7ドメイン × 最低3問 + 追加問題）
# =============================================================================

QUESTIONS = [
    # =========================================================================
    # Cloud Concepts（5問）
    # =========================================================================
    {
        "id": "q-cc-001",
        "course_id": "matsuyama-basic",
        "text": "松山城は標高132mの勝山山頂に建つ現存12天守の一つです。松山城の石垣のように、クラウドの基盤を支える概念として正しいものはどれですか？",
        "choice_1": "オンデマンドでリソースを調達できるセルフサービス",
        "choice_2": "常に同じサーバーを使い続ける固定割り当て",
        "choice_3": "利用者が物理サーバーを自分で設置する",
        "choice_4": "インターネットを使わずに通信する",
        "correct_choice_index": 0,
        "ehime_trivia": "松山城は加藤嘉明が1602年に築城を開始し、日本で12しかない現存天守の一つ。標高132mからは松山平野と瀬戸内海を一望できます。",
        "aws_ai_explanation": "クラウドコンピューティングの本質は「オンデマンド・セルフサービス」です。AWS では必要な時に必要なだけリソースを即座に調達でき、物理的なサーバー管理は不要です。",
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    },
    {
        "id": "q-cc-002",
        "course_id": "matsuyama-basic",
        "text": "道後温泉本館は利用者の増減に応じて浴室を使い分けます。このような需要変動への対応をクラウドでは何と呼びますか？",
        "choice_1": "レイテンシー",
        "choice_2": "エラスティシティ（弾力性）",
        "choice_3": "コンプライアンス",
        "choice_4": "レプリケーション",
        "correct_choice_index": 1,
        "ehime_trivia": "道後温泉本館は日本最古の温泉として知られ、夏目漱石の『坊っちゃん』にも登場。神の湯と霊の湯など複数の浴室があります。",
        "aws_ai_explanation": "エラスティシティ（弾力性）とは、需要の増減に応じてリソースを自動的にスケールアップ/ダウンできる能力です。AWS Auto Scaling がこの概念を実現します。",
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    },
    {
        "id": "q-cc-003",
        "course_id": "matsuyama-basic",
        "text": "みかん畑の収穫量は年によって変動します。AWSで「使った分だけ支払う」料金モデルを表す概念はどれですか？",
        "choice_1": "年間固定契約のみ",
        "choice_2": "従量課金（Pay-as-you-go）",
        "choice_3": "無料利用のみ",
        "choice_4": "前払い一括のみ",
        "correct_choice_index": 1,
        "ehime_trivia": "愛媛県は柑橘類の生産量日本一。温州みかんの収穫量は年間約12万トンで、全国シェアの約20%を占めています。",
        "aws_ai_explanation": "従量課金（Pay-as-you-go）はクラウドの基本原則の一つ。使った分だけ支払うため、初期投資を最小化しながら必要に応じてスケールできます。",
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    },
    {
        "id": "q-cc-004",
        "course_id": "matsuyama-basic",
        "text": "坊っちゃん列車は松山市内の決まったルートを巡回します。AWSのリージョンとアベイラビリティゾーンについて正しい説明はどれですか？",
        "choice_1": "リージョンは1つのデータセンターのみで構成される",
        "choice_2": "各リージョンは複数のアベイラビリティゾーンで構成され、障害に強い設計になっている",
        "choice_3": "アベイラビリティゾーンは世界に1つしかない",
        "choice_4": "リージョン間のデータ転送は常に無料である",
        "correct_choice_index": 1,
        "ehime_trivia": "坊っちゃん列車は、夏目漱石の小説に登場する汽車を復元したもの。松山市内の路面電車路線を走り、道後温泉まで観光客を運びます。",
        "aws_ai_explanation": "AWSリージョンは地理的に独立したエリアで、各リージョンは2つ以上のアベイラビリティゾーン（AZ）を持ちます。AZは独立した電源・ネットワークを持つデータセンター群です。",
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    },
    {
        "id": "q-cc-005",
        "course_id": "uwajima-intermediate",
        "text": "宇和島城は独立式の天守を持ち、他の建物に依存しません。AWSの「疎結合アーキテクチャ」の利点として正しいものはどれですか？",
        "choice_1": "全コンポーネントを1つのサーバーにまとめて管理が簡単になる",
        "choice_2": "コンポーネント間の依存性を減らし、一部の障害が全体に波及しにくくなる",
        "choice_3": "常にすべてのサービスが同時に起動する必要がある",
        "choice_4": "ネットワーク通信が不要になる",
        "correct_choice_index": 1,
        "ehime_trivia": "宇和島城は藤堂高虎が1601年に築城。現存12天守の一つで、独立式層塔型の天守が特徴。城山からは宇和海を望めます。",
        "aws_ai_explanation": "疎結合アーキテクチャでは、コンポーネント間の依存性を最小化します。Amazon SQSやSNSを使うことで、一部の障害が全体に影響しにくい耐障害性の高いシステムを構築できます。",
        "difficulty": "中級",
        "exam_domain": "Cloud Concepts",
    },
    # =========================================================================
    # Security and Compliance（5問）
    # =========================================================================
    {
        "id": "q-sc-001",
        "course_id": "uwajima-intermediate",
        "text": "宇和島の闘牛は入場時にチケットを確認されます。AWSでユーザーが「誰であるか」を確認するプロセスを何と呼びますか？",
        "choice_1": "認可（Authorization）",
        "choice_2": "認証（Authentication）",
        "choice_3": "暗号化（Encryption）",
        "choice_4": "監査（Auditing）",
        "correct_choice_index": 1,
        "ehime_trivia": "宇和島の闘牛は約300年の歴史があり、年5回の定期大会が開催されます。牛同士がぶつかり合う迫力ある伝統文化です。",
        "aws_ai_explanation": "認証（Authentication）は「あなたは誰か」を確認するプロセスです。AWS IAMではユーザー名/パスワードやMFAによる認証を行い、不正アクセスを防ぎます。",
        "difficulty": "中級",
        "exam_domain": "Security and Compliance",
    },
    {
        "id": "q-sc-002",
        "course_id": "uwajima-intermediate",
        "text": "愛媛県の真珠養殖場では、許可された作業者だけが特定のエリアに入れます。AWSで「何ができるか」を制御する仕組みはどれですか？",
        "choice_1": "Amazon S3",
        "choice_2": "IAMポリシー",
        "choice_3": "Amazon EC2",
        "choice_4": "AWS Lambda",
        "correct_choice_index": 1,
        "ehime_trivia": "愛媛県宇和島市は真珠養殖が盛んで、宇和海のリアス式海岸で良質な真珠が生産されています。全国有数の真珠産地です。",
        "aws_ai_explanation": "IAMポリシーは認可（Authorization）を制御します。JSON形式でどのリソースにどのアクションを許可/拒否するかを定義し、最小権限の原則を実現します。",
        "difficulty": "中級",
        "exam_domain": "Security and Compliance",
    },
    {
        "id": "q-sc-003",
        "course_id": "uwajima-intermediate",
        "text": "今治タオルの品質基準は厳格な認定制度で管理されています。AWSのコンプライアンスプログラムについて正しいものはどれですか？",
        "choice_1": "AWSは一切のコンプライアンス認証を取得していない",
        "choice_2": "AWSはISO 27001やSOC 2などの国際認証を取得し、AWS Artifactで証明書を確認できる",
        "choice_3": "コンプライアンスは利用者には関係なくAWSが全責任を負う",
        "choice_4": "コンプライアンス認証は毎月更新が必要である",
        "correct_choice_index": 1,
        "ehime_trivia": "今治タオルは独自の品質基準をクリアした製品だけがブランドマークを使用可能。5秒ルール（水に浮かべて5秒以内に沈む吸水性）が有名です。",
        "aws_ai_explanation": "AWSはISO 27001、SOC 1/2/3、PCI DSSなど多数の認証を取得。AWS Artifactから認証レポートをダウンロードでき、利用者の監査対応をサポートします。",
        "difficulty": "中級",
        "exam_domain": "Security and Compliance",
    },
    {
        "id": "q-sc-004",
        "course_id": "uwajima-intermediate",
        "text": "じゃこ天の製造工程では衛生管理のために各工程を記録します。AWSでAPIコールの履歴を記録するサービスはどれですか？",
        "choice_1": "Amazon RDS",
        "choice_2": "AWS CloudTrail",
        "choice_3": "Amazon VPC",
        "choice_4": "AWS Lambda",
        "correct_choice_index": 1,
        "ehime_trivia": "じゃこ天は愛媛県南予地方の郷土料理。小魚のすり身を揚げたもので、宇和島市や八幡浜市が名産地。そのまま食べても料理に使ってもおいしい。",
        "aws_ai_explanation": "AWS CloudTrailはAWSアカウント内のすべてのAPIコールを記録・監査するサービスです。誰が・いつ・何をしたかを追跡でき、セキュリティ分析やコンプライアンス監査に必須です。",
        "difficulty": "中級",
        "exam_domain": "Security and Compliance",
    },
    {
        "id": "q-sc-005",
        "course_id": "matsuyama-basic",
        "text": "道後温泉の貴重品ロッカーはデータを安全に保管します。AWSでデータを暗号化して保護するサービスはどれですか？",
        "choice_1": "AWS KMS（Key Management Service）",
        "choice_2": "Amazon Route 53",
        "choice_3": "AWS Auto Scaling",
        "choice_4": "Amazon CloudFront",
        "correct_choice_index": 0,
        "ehime_trivia": "道後温泉本館では、利用者は脱衣所のロッカーに貴重品を保管します。2024年に保存修理工事が完了し、新たな魅力を加えて営業再開しました。",
        "aws_ai_explanation": "AWS KMSは暗号鍵の作成・管理を行うサービスです。S3やEBSなどのデータを暗号化し、不正アクセスからデータを保護します。鍵のローテーションも自動化できます。",
        "difficulty": "基礎",
        "exam_domain": "Security and Compliance",
    },
    # =========================================================================
    # Cloud Technology and Services（5問）
    # =========================================================================
    {
        "id": "q-ct-001",
        "course_id": "matsuyama-basic",
        "text": "松山空港は旅客を目的地に運ぶハブです。AWSでウェブアプリケーションのトラフィックを複数サーバーに分散するサービスはどれですか？",
        "choice_1": "Amazon S3",
        "choice_2": "Elastic Load Balancing（ELB）",
        "choice_3": "Amazon Glacier",
        "choice_4": "AWS IAM",
        "correct_choice_index": 1,
        "ehime_trivia": "松山空港は愛媛県の空の玄関口で、東京・大阪・福岡等への路線があります。市街地から車で約20分とアクセスが良いのが特徴です。",
        "aws_ai_explanation": "Elastic Load Balancing（ELB）は、受信トラフィックを複数のターゲット（EC2インスタンスなど）に自動的に分散します。可用性と耐障害性を高める重要なサービスです。",
        "difficulty": "基礎",
        "exam_domain": "Cloud Technology and Services",
    },
    {
        "id": "q-ct-002",
        "course_id": "matsuyama-basic",
        "text": "松山市の路面電車は定められたルートに沿ってデータ（乗客）を運びます。AWSでリレーショナルデータベースを提供するマネージドサービスはどれですか？",
        "choice_1": "Amazon RDS",
        "choice_2": "Amazon SQS",
        "choice_3": "AWS Lambda",
        "choice_4": "Amazon CloudFront",
        "correct_choice_index": 0,
        "ehime_trivia": "松山市の路面電車（伊予鉄道）は1895年開業で日本最古級。市内を5路線で結び、市民の重要な足です。夏目漱石が乗った汽車のモデルでもあります。",
        "aws_ai_explanation": "Amazon RDSはMySQL、PostgreSQL、Oracleなどのリレーショナルデータベースをマネージドで提供します。バックアップ、パッチ適用、スケーリングをAWSが管理してくれます。",
        "difficulty": "基礎",
        "exam_domain": "Cloud Technology and Services",
    },
    {
        "id": "q-ct-003",
        "course_id": "shimanami-advanced",
        "text": "しまなみ海道の各島はそれぞれ独立しながらも橋で接続されています。マイクロサービスアーキテクチャの通信に適したAWSサービスはどれですか？",
        "choice_1": "Amazon SQS（Simple Queue Service）",
        "choice_2": "Amazon S3",
        "choice_3": "AWS IAM",
        "choice_4": "Amazon Glacier",
        "correct_choice_index": 0,
        "ehime_trivia": "しまなみ海道は愛媛県今治市と広島県尾道市を結ぶ全長約60kmの自動車道。6つの島を7つの橋で結び、サイクリングロードとしても世界的に有名です。",
        "aws_ai_explanation": "Amazon SQSはフルマネージドのメッセージキューサービスで、マイクロサービス間の非同期通信に使われます。疎結合アーキテクチャを実現し、各サービスを独立してスケールできます。",
        "difficulty": "上級",
        "exam_domain": "Cloud Technology and Services",
    },
    {
        "id": "q-ct-004",
        "course_id": "shimanami-advanced",
        "text": "今治市の造船所では設計図から効率的に船を組み立てます。AWSでインフラをコードとして管理するサービスはどれですか？",
        "choice_1": "AWS CloudFormation",
        "choice_2": "Amazon EC2",
        "choice_3": "Amazon S3",
        "choice_4": "AWS Direct Connect",
        "correct_choice_index": 0,
        "ehime_trivia": "今治市は日本最大の海事都市で、国内建造量の約18%を占めます。造船・海運業が地域経済の中心で、世界有数の造船技術を持ちます。",
        "aws_ai_explanation": "AWS CloudFormationはインフラをJSON/YAMLのテンプレートで定義し、自動的にプロビジョニングするIaC（Infrastructure as Code）サービスです。再現性のある環境構築が可能です。",
        "difficulty": "上級",
        "exam_domain": "Cloud Technology and Services",
    },
    {
        "id": "q-ct-005",
        "course_id": "shimanami-advanced",
        "text": "大島の村上海賊ミュージアムはデータを長期保存しています。AWSで低コストにデータを長期保管するサービスはどれですか？",
        "choice_1": "Amazon EC2",
        "choice_2": "Amazon S3 Glacier",
        "choice_3": "Amazon RDS",
        "choice_4": "AWS Lambda",
        "correct_choice_index": 1,
        "ehime_trivia": "村上海賊ミュージアムは今治市宮窪町にあり、戦国時代に瀬戸内海を支配した村上水軍の資料を展示。2014年に「日本遺産」第一号に認定されました。",
        "aws_ai_explanation": "Amazon S3 Glacierはアーカイブデータの長期保存に最適な低コストストレージです。アクセス頻度の低いデータを安価に保管でき、データ取り出しには時間がかかります。",
        "difficulty": "上級",
        "exam_domain": "Cloud Technology and Services",
    },
    # =========================================================================
    # Billing Pricing and Support（5問）
    # =========================================================================
    {
        "id": "q-bp-001",
        "course_id": "uwajima-intermediate",
        "text": "宇和島市の段畑ではスペースを効率的に使って作物を育てます。AWSのコスト最適化で「未使用リソースの削減」を支援するサービスはどれですか？",
        "choice_1": "AWS Trusted Advisor",
        "choice_2": "Amazon Route 53",
        "choice_3": "AWS Lambda",
        "choice_4": "Amazon VPC",
        "correct_choice_index": 0,
        "ehime_trivia": "宇和島市遊子の段畑は「耕して天に至る」と称される急斜面の石積み畑。じゃがいも栽培が盛んで、重要文化的景観にも選定されています。",
        "aws_ai_explanation": "AWS Trusted Advisorはコスト最適化、パフォーマンス、セキュリティ等の観点からAWS環境をチェックし、改善を推奨するサービスです。未使用のEC2やEBSを検出できます。",
        "difficulty": "中級",
        "exam_domain": "Billing Pricing and Support",
    },
    {
        "id": "q-bp-002",
        "course_id": "uwajima-intermediate",
        "text": "伊予鉄グループの定期券は期間を決めて購入すると割安になります。AWSで長期利用を約束することで割引を受けられる料金モデルはどれですか？",
        "choice_1": "オンデマンドインスタンス",
        "choice_2": "リザーブドインスタンス / Savings Plans",
        "choice_3": "スポットインスタンス",
        "choice_4": "Dedicated Hosts",
        "correct_choice_index": 1,
        "ehime_trivia": "伊予鉄グループは愛媛県最大の私鉄。路面電車・郊外電車・バスを運行し、松山市の公共交通の要です。ICカード「い〜カード」も発行しています。",
        "aws_ai_explanation": "リザーブドインスタンスやSavings Plansは1年〜3年の利用をコミットすることで最大72%の割引を受けられます。安定した利用が見込めるワークロードに最適です。",
        "difficulty": "中級",
        "exam_domain": "Billing Pricing and Support",
    },
    {
        "id": "q-bp-003",
        "course_id": "uwajima-intermediate",
        "text": "道の駅では地元農家が売上を個別に管理します。AWSで各サービスの利用料金を部門別に追跡できる機能はどれですか？",
        "choice_1": "AWS Cost Explorer のコスト配分タグ",
        "choice_2": "Amazon CloudWatch",
        "choice_3": "AWS Shield",
        "choice_4": "Amazon Kinesis",
        "correct_choice_index": 0,
        "ehime_trivia": "愛媛県内には30以上の道の駅があり、地元の農産物や特産品を販売。内子町の「フレッシュパークからり」は年間60万人が訪れる人気スポットです。",
        "aws_ai_explanation": "コスト配分タグを使うとAWSリソースにタグを付けて部門別・プロジェクト別にコストを追跡できます。AWS Cost Explorerで視覚的に分析し、コスト最適化に活用します。",
        "difficulty": "中級",
        "exam_domain": "Billing Pricing and Support",
    },
    {
        "id": "q-bp-004",
        "course_id": "matsuyama-basic",
        "text": "愛媛マラソンでは参加費無料の応援エリアがあります。AWSで無料で利用できるサポートプランはどれですか？",
        "choice_1": "エンタープライズプラン",
        "choice_2": "ビジネスプラン",
        "choice_3": "ベーシックプラン",
        "choice_4": "デベロッパープラン",
        "correct_choice_index": 2,
        "ehime_trivia": "愛媛マラソンは毎年2月に開催される市民マラソン大会。松山城を望むコースで約1万人が参加する四国最大級のマラソンイベントです。",
        "aws_ai_explanation": "AWSベーシックサポートプランは全ての利用者に無料で提供されます。ドキュメント、ホワイトペーパー、サポートフォーラムへのアクセス、およびサービスヘルスダッシュボードが含まれます。",
        "difficulty": "基礎",
        "exam_domain": "Billing Pricing and Support",
    },
    {
        "id": "q-bp-005",
        "course_id": "uwajima-intermediate",
        "text": "西条市の「うちぬき」は地下水が無料で湧き出しますが、水道には管理費がかかります。AWS無料利用枠について正しいものはどれですか？",
        "choice_1": "全サービスが永久に無料で使える",
        "choice_2": "一部サービスに12ヶ月の無料枠があり、それを超えると課金される",
        "choice_3": "無料利用枠は存在しない",
        "choice_4": "無料利用枠はエンタープライズ契約のみ適用される",
        "correct_choice_index": 1,
        "ehime_trivia": "西条市の「うちぬき」は自噴する地下水で、市内に約3,000本の自噴井があります。「日本の名水百選」に選ばれた良質な軟水が無料で汲めます。",
        "aws_ai_explanation": "AWS無料利用枠は3種類あります。12ヶ月無料（EC2 t2.micro等）、常に無料（Lambda月100万リクエスト等）、トライアル（一部サービスの短期無料）です。",
        "difficulty": "中級",
        "exam_domain": "Billing Pricing and Support",
    },
    # =========================================================================
    # AI and ML Fundamentals（5問）
    # =========================================================================
    {
        "id": "q-ai-001",
        "course_id": "dogo-ai-basic",
        "text": "道後温泉では過去の入浴客数データから混雑を予測できます。データから予測モデルを自動的に学習する技術を何と呼びますか？",
        "choice_1": "手動プログラミング",
        "choice_2": "機械学習（Machine Learning）",
        "choice_3": "データベース管理",
        "choice_4": "ネットワーク設計",
        "correct_choice_index": 1,
        "ehime_trivia": "道後温泉は3000年以上の歴史を持つ日本最古の温泉の一つ。聖徳太子も入浴したと伝わり、年間約80万人が訪れる松山市最大の観光スポットです。",
        "aws_ai_explanation": "機械学習は大量のデータからパターンを自動的に学習し、予測モデルを構築する技術です。Amazon SageMakerを使えば、MLモデルの構築・訓練・デプロイが容易に行えます。",
        "difficulty": "基礎",
        "exam_domain": "AI and ML Fundamentals",
    },
    {
        "id": "q-ai-002",
        "course_id": "dogo-ai-basic",
        "text": "みかんの選果場では大きさ・色・形で等級を分けます。同様にデータをカテゴリに分類するMLタスクを何と呼びますか？",
        "choice_1": "回帰（Regression）",
        "choice_2": "分類（Classification）",
        "choice_3": "クラスタリング（Clustering）",
        "choice_4": "強化学習（Reinforcement Learning）",
        "correct_choice_index": 1,
        "ehime_trivia": "愛媛のみかん選果場では光センサーで糖度・酸度を計測し、自動で等級分けを行います。甘さを数値化する技術で高品質なみかんを出荷しています。",
        "aws_ai_explanation": "分類はデータを事前定義されたカテゴリに振り分ける教師あり学習タスクです。スパム判定、画像認識、感情分析などに使われます。Amazon Comprehendは文書分類を提供します。",
        "difficulty": "基礎",
        "exam_domain": "AI and ML Fundamentals",
    },
    {
        "id": "q-ai-003",
        "course_id": "dogo-ai-basic",
        "text": "坊っちゃん団子は3色の団子を串に刺して提供します。MLモデル開発の3つの主要ステップとして正しいものはどれですか？",
        "choice_1": "設計 → テスト → 納品",
        "choice_2": "データ収集・前処理 → モデル訓練 → 評価・デプロイ",
        "choice_3": "企画 → 営業 → 販売",
        "choice_4": "ハードウェア購入 → ソフトウェアインストール → 運用",
        "correct_choice_index": 1,
        "ehime_trivia": "坊っちゃん団子は夏目漱石『坊っちゃん』に因んだ松山銘菓。抹茶（緑）・卵（黄）・小豆（茶）の3色で、一口サイズの串団子です。",
        "aws_ai_explanation": "MLパイプラインは「データ準備→訓練→デプロイ」の3段階が基本。Amazon SageMakerはこの全工程をカバーし、データラベリングからエンドポイント公開まで一貫して行えます。",
        "difficulty": "基礎",
        "exam_domain": "AI and ML Fundamentals",
    },
    {
        "id": "q-ai-004",
        "course_id": "shimanami-advanced",
        "text": "今治のタオル工場では不良品をセンサーで自動検出します。AWSで画像中の異常を検出するMLサービスはどれですか？",
        "choice_1": "Amazon Rekognition",
        "choice_2": "Amazon S3",
        "choice_3": "AWS CloudFormation",
        "choice_4": "Amazon Route 53",
        "correct_choice_index": 0,
        "ehime_trivia": "今治タオルの製造では、織り上がったタオルを一枚一枚検品します。近年はAI画像認識を活用した自動検品システムの導入も進んでいます。",
        "aws_ai_explanation": "Amazon Rekognitionは画像・動画分析サービスで、物体検出、顔認識、テキスト検出などが可能です。製造業での不良品検出や品質管理にも活用されています。",
        "difficulty": "上級",
        "exam_domain": "AI and ML Fundamentals",
    },
    {
        "id": "q-ai-005",
        "course_id": "shimanami-advanced",
        "text": "瀬戸内海の潮流データを時系列で分析し、最適な航行ルートを予測したい場合に使うMLアプローチはどれですか？",
        "choice_1": "教師なし学習のクラスタリング",
        "choice_2": "時系列予測（Time Series Forecasting）",
        "choice_3": "画像分類",
        "choice_4": "自然言語処理",
        "correct_choice_index": 1,
        "ehime_trivia": "来島海峡は潮流の速さで知られ、最大時速10ノット以上。しまなみ海道の来島海峡大橋からは渦潮が見えることもあり、船舶は潮流に合わせて航行します。",
        "aws_ai_explanation": "時系列予測は過去の時間的パターンから将来を予測するMLタスクです。Amazon Forecastは時系列予測の専用サービスで、需要予測や在庫計画に活用されています。",
        "difficulty": "上級",
        "exam_domain": "AI and ML Fundamentals",
    },
    # =========================================================================
    # Generative AI（5問）
    # =========================================================================
    {
        "id": "q-ga-001",
        "course_id": "dogo-ai-basic",
        "text": "松山市の俳句ポストには誰でも自由に俳句を投函できます。人間のように文章を生成するAI技術の総称は何ですか？",
        "choice_1": "ルールベースシステム",
        "choice_2": "生成AI（Generative AI）",
        "choice_3": "リレーショナルデータベース",
        "choice_4": "ファイアウォール",
        "correct_choice_index": 1,
        "ehime_trivia": "松山市は正岡子規の出身地として「俳句の都」と呼ばれ、市内約90箇所に俳句ポストが設置されています。毎年「俳句甲子園」も開催されます。",
        "aws_ai_explanation": "生成AIは新しいコンテンツ（テキスト、画像、コード等）を生成する技術です。Amazon Bedrockは複数の基盤モデル（Claude、Titan等）へのAPIアクセスを提供します。",
        "difficulty": "基礎",
        "exam_domain": "Generative AI",
    },
    {
        "id": "q-ga-002",
        "course_id": "dogo-ai-basic",
        "text": "夏目漱石の文体を学習して新しい小説を書くAIがあるとします。このようなモデルの基盤技術は何ですか？",
        "choice_1": "SQL データベース",
        "choice_2": "大規模言語モデル（LLM）",
        "choice_3": "スプレッドシート",
        "choice_4": "ファイルサーバー",
        "correct_choice_index": 1,
        "ehime_trivia": "夏目漱石は松山中学の英語教師として1895年に赴任。この経験を基に『坊っちゃん』を執筆し、松山は文学の街として知られるようになりました。",
        "aws_ai_explanation": "大規模言語モデル（LLM）は膨大なテキストデータで訓練された基盤モデルです。Amazon Bedrockでは Claude、Amazon Titan 等のLLMを API経由で利用できます。",
        "difficulty": "基礎",
        "exam_domain": "Generative AI",
    },
    {
        "id": "q-ga-003",
        "course_id": "shimanami-advanced",
        "text": "今治市の観光案内AIチャットボットを構築したい場合、Amazon Bedrockで最も適切なアプローチはどれですか？",
        "choice_1": "基盤モデルをゼロから自分で訓練する",
        "choice_2": "RAG（Retrieval Augmented Generation）で地域情報を基盤モデルに提供する",
        "choice_3": "データベースに直接質問文を保存する",
        "choice_4": "画像生成モデルを使用する",
        "correct_choice_index": 1,
        "ehime_trivia": "今治市は2023年からAIを活用した観光案内の実証実験を行っています。しまなみ海道のサイクリング情報や今治城の歴史をAIが多言語で案内する取り組みです。",
        "aws_ai_explanation": "RAGは外部知識ベースの情報を検索し、基盤モデルの回答に組み込む手法です。Amazon Bedrock Knowledge Basesを使えば、独自データを活用した正確なAI応答を実現できます。",
        "difficulty": "上級",
        "exam_domain": "Generative AI",
    },
    {
        "id": "q-ga-004",
        "course_id": "shimanami-advanced",
        "text": "愛媛県の方言「〜やけん」を理解するAIを作りたい。基盤モデルを特定のタスクに適応させる手法は何ですか？",
        "choice_1": "ファインチューニング（Fine-tuning）",
        "choice_2": "データベースの正規化",
        "choice_3": "ネットワークの暗号化",
        "choice_4": "ロードバランシング",
        "correct_choice_index": 0,
        "ehime_trivia": "伊予弁は「〜やけん（だから）」「〜ぞなもし（ですよ）」などが特徴的。地域によって中予弁・南予弁・東予弁に分かれ、それぞれ微妙に異なります。",
        "aws_ai_explanation": "ファインチューニングは事前訓練済みモデルを特定のドメインやタスクに合わせて追加訓練する手法です。Amazon Bedrockではカスタムモデルの作成が可能で、独自データで精度を向上できます。",
        "difficulty": "上級",
        "exam_domain": "Generative AI",
    },
    {
        "id": "q-ga-005",
        "course_id": "dogo-ai-basic",
        "text": "松山市の観光パンフレットをAIで多言語化したい。プロンプトエンジニアリングの基本原則として正しいものはどれですか？",
        "choice_1": "できるだけ曖昧な指示を出す",
        "choice_2": "具体的な指示と出力形式を明示し、コンテキストを提供する",
        "choice_3": "一度に全ての言語を同時に要求する",
        "choice_4": "モデルにフィードバックを一切与えない",
        "correct_choice_index": 1,
        "ehime_trivia": "松山市は外国人観光客も増加中で、道後温泉・松山城の多言語案内が進んでいます。2023年は年間約15万人の外国人観光客が愛媛を訪れました。",
        "aws_ai_explanation": "プロンプトエンジニアリングでは、明確な指示、具体的な出力形式、適切なコンテキスト提供が重要です。Few-shot例の提示やシステムプロンプトの活用で応答品質を向上させます。",
        "difficulty": "基礎",
        "exam_domain": "Generative AI",
    },
    # =========================================================================
    # Responsible AI（3問）
    # =========================================================================
    {
        "id": "q-ra-001",
        "course_id": "shimanami-advanced",
        "text": "愛媛県の防災AIシステムが特定地域の住民だけを優先避難させるバイアスがあった場合、これはAI倫理のどの原則に反しますか？",
        "choice_1": "スケーラビリティ",
        "choice_2": "公平性（Fairness）",
        "choice_3": "可用性",
        "choice_4": "パフォーマンス",
        "correct_choice_index": 1,
        "ehime_trivia": "愛媛県は南海トラフ地震への備えとして防災対策を強化。2018年の西日本豪雨では大洲市・西予市で甚大な被害を受け、防災AIの活用が議論されています。",
        "aws_ai_explanation": "AI の公平性は、モデルが特定のグループに対して偏った判断をしないことを求めます。Amazon SageMaker Clarifyはモデルのバイアスを検出し、説明可能性を提供します。",
        "difficulty": "上級",
        "exam_domain": "Responsible AI",
    },
    {
        "id": "q-ra-002",
        "course_id": "shimanami-advanced",
        "text": "みかん農家向けAI病害診断アプリが誤診断した場合に備え、必要な責任あるAIの原則はどれですか？",
        "choice_1": "AIの判断を絶対視し人間は介入しない",
        "choice_2": "説明可能性（Explainability）と人間による監視",
        "choice_3": "データを全て削除する",
        "choice_4": "AIの利用を完全に停止する",
        "correct_choice_index": 1,
        "ehime_trivia": "愛媛のみかん農家ではAIによる病害虫の早期発見の研究が進んでいます。かいよう病やそうか病などの柑橘類の病気を画像から自動検出する技術です。",
        "aws_ai_explanation": "説明可能性はAIの判断根拠を人間が理解できることを指します。重要な判断には Human-in-the-Loop（人間による監視）を組み込み、AIの誤りを検出・修正する仕組みが必要です。",
        "difficulty": "上級",
        "exam_domain": "Responsible AI",
    },
    {
        "id": "q-ra-003",
        "course_id": "dogo-ai-basic",
        "text": "道後温泉の利用者データをAI分析に使う際、個人情報保護の観点から最も重要なことはどれですか？",
        "choice_1": "データを全て公開する",
        "choice_2": "利用者の同意を得て、適切にデータを匿名化してから使用する",
        "choice_3": "AI精度のためにデータを無制限に収集する",
        "choice_4": "データの出典を隠す",
        "correct_choice_index": 1,
        "ehime_trivia": "道後温泉は年間約80万人が利用。入浴客の動向データは観光戦略に活用されていますが、個人が特定されないよう統計データとして処理されています。",
        "aws_ai_explanation": "責任あるAIではデータプライバシーが最重要原則の一つ。利用者の同意取得、データの匿名化・最小化、目的外利用の禁止が基本です。AWSではAmazon Macie等でデータ保護を支援します。",
        "difficulty": "基礎",
        "exam_domain": "Responsible AI",
    },
]


# =============================================================================
# シーディング関数
# =============================================================================


def seed_database(db_session: Session) -> bool:
    """
    データベースに初期データを投入する。

    既にコースデータが存在する場合はスキップする（冪等性を確保）。

    Args:
        db_session: SQLAlchemy セッション

    Returns:
        True: シーディング実行, False: スキップ（データ既存）
    """
    # 既にデータが存在する場合はスキップ
    existing_courses = db_session.query(CourseModel).count()
    if existing_courses > 0:
        return False

    # コースの投入
    for course_data in COURSES:
        course = CourseModel(
            id=course_data["id"],
            name=course_data["name"],
            region=course_data["region"],
            difficulty=course_data["difficulty"],
            description=course_data["description"],
        )
        db_session.add(course)

    # 問題の投入
    for question_data in QUESTIONS:
        question = QuestionModel(
            id=question_data["id"],
            course_id=question_data["course_id"],
            text=question_data["text"],
            choice_1=question_data["choice_1"],
            choice_2=question_data["choice_2"],
            choice_3=question_data["choice_3"],
            choice_4=question_data["choice_4"],
            correct_choice_index=question_data["correct_choice_index"],
            ehime_trivia=question_data["ehime_trivia"],
            aws_ai_explanation=question_data["aws_ai_explanation"],
            difficulty=question_data["difficulty"],
            exam_domain=question_data["exam_domain"],
        )
        db_session.add(question)

    db_session.commit()
    return True
