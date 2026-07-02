# Requirements Document

## Introduction

愛媛探索AIクイズアプリケーションに対する3つの改善を行う。(1) 難易度と地域の対応関係を修正し、南予→中予→東予の順で初級→中級→上級となるようにする。(2) 用語集（グロサリー）を拡充し、クイズ問題・選択肢に登場するすべての技術用語をカバーする。(3) ライセンスページに愛媛県オープンデータ、文化財データ、AWS公式ドキュメント、AI用語参考文献、AWS学習リソースの帰属情報を追加する。

## Glossary

- **Quiz_Application**: 愛媛探索AIクイズ（FastAPI + SQLAlchemy + Jinja2 + HTMXで構築されたWebアプリケーション）
- **Region_Enum**: アプリ内でクイズの地域・難易度区分を表すPython Enumクラス（app/domain/models.py内で定義）
- **Glossary_Seed**: 用語集の初期データを格納するPythonモジュール（app/data/glossary_seed.py）
- **GlossaryTermModel**: データベース上の用語集エンティティを表すSQLAlchemyモデル
- **License_Page**: アプリケーションの/licensesパスで表示されるライセンス・クレジット表記ページ
- **Difficulty_Order**: 難易度の進行順序（初級→中級→上級）
- **SVG_Map**: トップ画面で表示される愛媛県の地域別SVGマップ
- **Course_Panel**: マップクリック時に表示されるコース一覧パネル

## Requirements

### Requirement 1: 難易度と地域の対応関係修正

**User Story:** As a クイズ利用者, I want 南予が初級・中予が中級・東予が上級として表示される, so that 地理的な進行（西から東へ）と難易度上昇が一致し直感的に学習を進められる。

#### Acceptance Criteria

1. THE Region_Enum SHALL assign the value "初級" to NANYO, "中級" to CHUYO, and "上級" to TOYO.
2. WHEN the SVG_Map is rendered, THE Quiz_Application SHALL display regions in the order 南予（初級）, 中予（中級）, 東予（上級） from left to right in the tab list.
3. WHEN a user iterates through difficulty levels, THE Quiz_Application SHALL present them in the progression 初級 → 中級 → 上級 corresponding to 南予 → 中予 → 東予.
4. THE Region_Enum SHALL define members in the order NANYO, CHUYO, TOYO so that Python iteration order matches the intended difficulty progression.
5. WHEN the Course_Panel displays course metadata, THE Quiz_Application SHALL show the correct difficulty label matching the updated Region_Enum values.

### Requirement 2: 用語集の網羅的拡充

**User Story:** As a クイズ利用者, I want クイズ問題と選択肢に登場するすべての技術用語が用語集に掲載されている, so that 知らない用語をいつでも学習ページで確認できる。

#### Acceptance Criteria

1. THE Glossary_Seed SHALL contain entries for all AWS service names that appear in quiz questions and answer choices, including but not limited to: Amazon EC2, Amazon S3, AWS Lambda, Amazon RDS, Amazon DynamoDB, Amazon VPC, AWS IAM, Amazon CloudFront, Amazon SageMaker, Amazon Bedrock, Amazon Route 53, Amazon SQS, AWS CloudFormation, Elastic Load Balancing, Amazon S3 Glacier, AWS KMS, Amazon Rekognition, and Amazon Comprehend.
2. THE Glossary_Seed SHALL contain entries for all cloud computing concepts that appear in quiz questions and answer choices, including but not limited to: スケーラビリティ, 可用性, 共有責任モデル, Well-Architected Framework, 従量課金, リージョン, アベイラビリティゾーン, CDN, サーバーレス, and マネージドサービス.
3. THE Glossary_Seed SHALL contain entries for all AI and machine learning concepts that appear in quiz questions and answer choices, including but not limited to: 機械学習, 深層学習, 大規模言語モデル（LLM）, ニューラルネットワーク, プロンプトエンジニアリング, ファインチューニング, 転移学習, 教師あり学習, 教師なし学習, and 強化学習.
4. THE Glossary_Seed SHALL contain entries for all security concepts that appear in quiz questions and answer choices, including but not limited to: 多要素認証（MFA）, 暗号化, IAMポリシー, セキュリティグループ, and 最小権限の原則.
5. WHEN a new glossary term is added, THE Glossary_Seed SHALL include a category, sort_order, term name, and description for each entry.
6. THE Glossary_Seed SHALL organize terms into logical categories with sequential sort_order values within each category.
7. THE Quiz_Application SHALL display all glossary terms on the /study page grouped by category.

### Requirement 3: ライセンスページの帰属情報拡充

**User Story:** As a 開発者, I want ライセンスページにすべてのデータソースと参考文献の帰属情報が記載されている, so that 著作権・ライセンス要件を適切に満たせる。

#### Acceptance Criteria

1. THE License_Page SHALL display attribution for 愛媛県オープンデータ with the license type CC BY 4.0 and the URL https://www.pref.ehime.jp/opendata-catalog/.
2. THE License_Page SHALL display attribution for 愛媛県文化財データ with URLs https://www.pref.ehime.jp/site/ehimenotakara/ and https://ehime-kyoiku.esnet.ed.jp/bunkazai/shitei-itiran.
3. THE License_Page SHALL display attribution for AWS official documentation including exam guides, service documentation pages, and whitepapers.
4. THE License_Page SHALL display attribution for AI glossary reference sources including Stanford HAI, MIT Media Lab, and Wikipedia.
5. THE License_Page SHALL display attribution for AWS training resources including AWS Skill Builder and AWS Cloud Practitioner Essentials.
6. THE License_Page SHALL retain all existing attribution entries (愛媛県地図データ by Lincun under CC BY-SA 3.0, HTMX, Tailwind CSS, FastAPI).
7. WHEN the License_Page is rendered, THE Quiz_Application SHALL display each attribution entry with the source name, license type or usage terms, and a hyperlink to the original source where applicable.
8. THE License_Page SHALL be accessible at the /licenses URL path and render correctly with the existing Jinja2 template system.
