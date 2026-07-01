"""
愛媛探索AIクイズ - 用語集シードデータ

CLF-C02（AWS Certified Cloud Practitioner）およびAIF-C01（AWS Certified AI Practitioner）
試験範囲のAWSサービス名・クラウド用語・AI/ML概念を網羅する用語集データ。
用語を追加・編集する場合はこのファイルだけを変更する。
"""

import uuid

from sqlalchemy.orm import Session

from app.data.models import GlossaryTermModel

GLOSSARY_SEED_DATA: list[dict] = [
    # =========================================================================
    # クラウド基礎（15語）
    # =========================================================================
    {"category": "クラウド基礎", "sort_order": 1, "term": "クラウドコンピューティング", "description": "インターネット経由でサーバー・ストレージ・データベースなどのITリソースをオンデマンドで利用できるサービス提供形態。"},
    {"category": "クラウド基礎", "sort_order": 2, "term": "オンプレミス", "description": "自社内にサーバーやネットワーク機器を設置・運用する従来型のIT基盤。クラウドと対比して使われる用語。"},
    {"category": "クラウド基礎", "sort_order": 3, "term": "リージョン", "description": "AWSがデータセンター群を配置する地理的な区域。東京リージョンなど世界各地に存在し、レイテンシやデータ所在地を考慮して選択する。"},
    {"category": "クラウド基礎", "sort_order": 4, "term": "アベイラビリティゾーン", "description": "リージョン内にある物理的に独立したデータセンター群。複数AZにリソースを分散配置することで高可用性を確保する。"},
    {"category": "クラウド基礎", "sort_order": 5, "term": "エッジロケーション", "description": "CloudFrontなどのCDNサービスがコンテンツをキャッシュするための世界各地に分散されたサーバー拠点。"},
    {"category": "クラウド基礎", "sort_order": 6, "term": "スケーラビリティ", "description": "需要に応じてシステムのリソースを柔軟に拡張・縮小できる性質。クラウドの主要な利点のひとつ。"},
    {"category": "クラウド基礎", "sort_order": 7, "term": "高可用性", "description": "システムが障害発生時にも極力ダウンタイムなしで稼働し続けること。99.99%以上の稼働率を目指す設計。"},
    {"category": "クラウド基礎", "sort_order": 8, "term": "耐障害性", "description": "システムの一部が故障しても全体としてのサービス提供を継続できる能力。冗長構成により実現する。"},
    {"category": "クラウド基礎", "sort_order": 9, "term": "弾力性（Elasticity）", "description": "負荷の変動に応じてリソースを自動的に増減させる能力。Auto Scalingなどのサービスで実現される。"},
    {"category": "クラウド基礎", "sort_order": 10, "term": "従量課金", "description": "使った分だけ料金を支払う課金モデル。初期費用不要で、必要なリソースを必要な時間だけ利用できる。"},
    {"category": "クラウド基礎", "sort_order": 11, "term": "Well-Architected Framework", "description": "AWSが提唱するクラウド設計のベストプラクティス集。運用上の優秀性・セキュリティ・信頼性・パフォーマンス効率・コスト最適化・持続可能性の6本柱で構成。"},
    {"category": "クラウド基礎", "sort_order": 12, "term": "共有責任モデル", "description": "AWSとユーザーがセキュリティの責任を分担する考え方。AWSがインフラの物理セキュリティを担い、ユーザーがOS設定やデータ管理を担う。"},
    {"category": "クラウド基礎", "sort_order": 13, "term": "サーバーレス", "description": "サーバーの管理・プロビジョニングが不要なクラウド実行モデル。開発者はコード記述に集中でき、インフラ運用はAWSが担う。"},
    {"category": "クラウド基礎", "sort_order": 14, "term": "マネージドサービス", "description": "インフラの運用・保守・パッチ適用などをAWSが代行するサービス形態。ユーザーはビジネスロジックに集中できる。"},
    {"category": "クラウド基礎", "sort_order": 15, "term": "IaC（Infrastructure as Code）", "description": "インフラ構成をコードとして記述・管理する手法。再現性・バージョン管理・自動化が実現できる。"},
    # =========================================================================
    # AWSコンピューティング（12語）
    # =========================================================================
    {"category": "AWSコンピューティング", "sort_order": 1, "term": "Amazon EC2", "description": "AWSの仮想サーバーサービス。OSやスペックを自由に選択して起動でき、Webサーバーやアプリケーション基盤として使われる。"},
    {"category": "AWSコンピューティング", "sort_order": 2, "term": "AWS Lambda", "description": "サーバーを管理せずにコードを実行できるサーバーレスコンピューティングサービス。イベント駆動で動作し実行時間単位で課金される。"},
    {"category": "AWSコンピューティング", "sort_order": 3, "term": "Amazon ECS", "description": "Dockerコンテナを管理・実行するフルマネージドコンテナオーケストレーションサービス。FargateやEC2でコンテナを稼働できる。"},
    {"category": "AWSコンピューティング", "sort_order": 4, "term": "Amazon EKS", "description": "マネージドKubernetesサービス。Kubernetesのコントロールプレーンの管理をAWSが担い、コンテナのオーケストレーションを簡素化する。"},
    {"category": "AWSコンピューティング", "sort_order": 5, "term": "AWS Fargate", "description": "ECSやEKSで使用するサーバーレスコンピューティングエンジン。コンテナ実行時にサーバーの管理が不要になる。"},
    {"category": "AWSコンピューティング", "sort_order": 6, "term": "Auto Scaling", "description": "需要の変動に応じてEC2インスタンス数を自動調整する機能。負荷増大時にスケールアウトし、低負荷時にスケールインする。"},
    {"category": "AWSコンピューティング", "sort_order": 7, "term": "Elastic Beanstalk", "description": "アプリケーションのデプロイと管理を自動化するPaaSサービス。インフラ設定なしでWebアプリケーションを公開できる。"},
    {"category": "AWSコンピューティング", "sort_order": 8, "term": "AWS Batch", "description": "バッチコンピューティングジョブの実行を効率的に管理するサービス。ジョブのキューイング、スケジューリング、リソース割り当てを自動化する。"},
    {"category": "AWSコンピューティング", "sort_order": 9, "term": "Amazon Lightsail", "description": "シンプルなVPSサービス。小規模Webサイトやアプリケーションを低コストで素早くデプロイできる。"},
    {"category": "AWSコンピューティング", "sort_order": 10, "term": "AWS Step Functions", "description": "複数のAWSサービスをワークフローとして視覚的に連携・実行するサーバーレスオーケストレーションサービス。"},
    {"category": "AWSコンピューティング", "sort_order": 11, "term": "Amazon SQS", "description": "フルマネージドのメッセージキューイングサービス。分散システム間の非同期メッセージングを実現し、疎結合アーキテクチャを構築する。"},
    {"category": "AWSコンピューティング", "sort_order": 12, "term": "Amazon SNS", "description": "フルマネージドのPub/Subメッセージングサービス。通知メッセージを複数のサブスクライバーに同時配信できる。"},
    # =========================================================================
    # AWSストレージ・データベース（15語）
    # =========================================================================
    {"category": "AWSストレージ・データベース", "sort_order": 1, "term": "Amazon S3", "description": "AWSのオブジェクトストレージサービス。容量無制限で99.999999999%の耐久性を持ち、画像・動画・バックアップなど任意のファイルを保存できる。"},
    {"category": "AWSストレージ・データベース", "sort_order": 2, "term": "Amazon EBS", "description": "EC2インスタンスにアタッチして使用するブロックストレージサービス。永続的なデータ保存が可能で、スナップショットによるバックアップもできる。"},
    {"category": "AWSストレージ・データベース", "sort_order": 3, "term": "Amazon EFS", "description": "複数のEC2インスタンスから同時にアクセス可能なフルマネージドNFSファイルシステム。自動でスケールする。"},
    {"category": "AWSストレージ・データベース", "sort_order": 4, "term": "Amazon S3 Glacier", "description": "低コストの長期アーカイブストレージサービス。アクセス頻度が低いデータのバックアップやコンプライアンス保存に最適。"},
    {"category": "AWSストレージ・データベース", "sort_order": 5, "term": "Amazon RDS", "description": "MySQL・PostgreSQL・Auroraなどのリレーショナルデータベースをマネージドで提供するサービス。バックアップやパッチ適用をAWSが代行する。"},
    {"category": "AWSストレージ・データベース", "sort_order": 6, "term": "Amazon Aurora", "description": "AWSが設計したクラウドネイティブなリレーショナルDB。MySQL/PostgreSQL互換で、商用DB並みの性能をオープンソースの価格で実現する。"},
    {"category": "AWSストレージ・データベース", "sort_order": 7, "term": "Amazon DynamoDB", "description": "フルマネージドのNoSQLデータベースサービス。ミリ秒単位の低レイテンシでキーバリュー型のデータアクセスを提供する。"},
    {"category": "AWSストレージ・データベース", "sort_order": 8, "term": "Amazon ElastiCache", "description": "RedisやMemcachedに対応するインメモリキャッシュサービス。データベースの負荷を軽減し、アプリケーションの応答速度を高速化する。"},
    {"category": "AWSストレージ・データベース", "sort_order": 9, "term": "Amazon Redshift", "description": "ペタバイト規模のデータウェアハウスサービス。大量データの分析クエリを高速に実行できるカラムナーストレージを採用している。"},
    {"category": "AWSストレージ・データベース", "sort_order": 10, "term": "Amazon Neptune", "description": "フルマネージドのグラフデータベースサービス。関連性の高いデータセットのクエリを高速に処理できる。"},
    {"category": "AWSストレージ・データベース", "sort_order": 11, "term": "Amazon DocumentDB", "description": "MongoDB互換のフルマネージドドキュメントデータベースサービス。JSONライクなドキュメントデータの保存・検索に適している。"},
    {"category": "AWSストレージ・データベース", "sort_order": 12, "term": "AWS Storage Gateway", "description": "オンプレミスのアプリケーションからAWSのクラウドストレージへシームレスにアクセスできるハイブリッドストレージサービス。"},
    {"category": "AWSストレージ・データベース", "sort_order": 13, "term": "Amazon Athena", "description": "S3に保存されたデータに対して標準SQLで直接クエリを実行できるサーバーレス分析サービス。ETL不要でデータ分析が可能。"},
    {"category": "AWSストレージ・データベース", "sort_order": 14, "term": "AWS DMS", "description": "Database Migration Serviceの略。オンプレミスやクラウドのデータベースをAWSへ最小限のダウンタイムで移行するサービス。"},
    {"category": "AWSストレージ・データベース", "sort_order": 15, "term": "Amazon Keyspaces", "description": "Apache Cassandra互換のフルマネージドNoSQLデータベースサービス。大規模な時系列データやIoTデータの処理に適している。"},
    # =========================================================================
    # AWSネットワーキング（10語）
    # =========================================================================
    {"category": "AWSネットワーキング", "sort_order": 1, "term": "Amazon VPC", "description": "AWS上に論理的に分離された仮想ネットワークを構築するサービス。サブネット・ルートテーブル・ゲートウェイで環境を制御する。"},
    {"category": "AWSネットワーキング", "sort_order": 2, "term": "Amazon CloudFront", "description": "AWSのCDNサービス。世界中のエッジロケーションからWebコンテンツを低レイテンシで高速配信する。"},
    {"category": "AWSネットワーキング", "sort_order": 3, "term": "Amazon Route 53", "description": "AWSのDNSサービス。ドメイン登録・DNSルーティング・ヘルスチェックを提供し、高可用性のトラフィック管理を実現する。"},
    {"category": "AWSネットワーキング", "sort_order": 4, "term": "Elastic Load Balancing", "description": "受信トラフィックを複数のターゲットに自動分散するロードバランサーサービス。ALB・NLB・CLBの3種類がある。"},
    {"category": "AWSネットワーキング", "sort_order": 5, "term": "AWS Direct Connect", "description": "オンプレミスのデータセンターとAWSを専用線で接続するサービス。インターネットを経由しないため安定した通信が可能。"},
    {"category": "AWSネットワーキング", "sort_order": 6, "term": "AWS VPN", "description": "オンプレミスネットワークとAWS VPCをインターネット経由の暗号化トンネルで接続するサービス。低コストなハイブリッド接続手段。"},
    {"category": "AWSネットワーキング", "sort_order": 7, "term": "NATゲートウェイ", "description": "プライベートサブネットのリソースがインターネットへ接続する際に使うアドレス変換サービス。外部からの直接アクセスは遮断する。"},
    {"category": "AWSネットワーキング", "sort_order": 8, "term": "セキュリティグループ", "description": "EC2インスタンスなどへのネットワークトラフィックを制御する仮想ファイアウォール。ステートフルにインバウンド・アウトバウンドを管理する。"},
    {"category": "AWSネットワーキング", "sort_order": 9, "term": "AWS Transit Gateway", "description": "複数のVPCやオンプレミスネットワークを中央ハブとして相互接続するサービス。大規模ネットワークの管理を簡素化する。"},
    {"category": "AWSネットワーキング", "sort_order": 10, "term": "AWS Global Accelerator", "description": "AWSグローバルネットワークを活用してアプリケーションの可用性とパフォーマンスを向上させるネットワークサービス。"},
    # =========================================================================
    # AWSセキュリティ（15語）
    # =========================================================================
    {"category": "AWSセキュリティ", "sort_order": 1, "term": "AWS IAM", "description": "AWSリソースへのアクセスを安全に管理するサービス。ユーザー・グループ・ロール・ポリシーを用いて認証と認可を制御する。"},
    {"category": "AWSセキュリティ", "sort_order": 2, "term": "AWS KMS", "description": "暗号鍵の作成・管理を行うマネージドサービス。AWSサービスやアプリケーションのデータ暗号化に使う鍵を一元管理できる。"},
    {"category": "AWSセキュリティ", "sort_order": 3, "term": "AWS Shield", "description": "DDoS攻撃からアプリケーションを保護するマネージドサービス。Standard版は全AWSユーザーに無料で提供される。"},
    {"category": "AWSセキュリティ", "sort_order": 4, "term": "AWS WAF", "description": "Webアプリケーションファイアウォール。SQLインジェクションやXSSなどの一般的なWeb攻撃からアプリケーションを保護する。"},
    {"category": "AWSセキュリティ", "sort_order": 5, "term": "Amazon GuardDuty", "description": "AWSアカウントやワークロードに対する脅威をAI/MLで自動検知するマネージド脅威検出サービス。"},
    {"category": "AWSセキュリティ", "sort_order": 6, "term": "Amazon Inspector", "description": "EC2インスタンスやコンテナの脆弱性を自動スキャンして検出するセキュリティ評価サービス。"},
    {"category": "AWSセキュリティ", "sort_order": 7, "term": "Amazon Macie", "description": "S3に保存された機密データ（個人情報など）を機械学習で自動検出・分類・保護するデータセキュリティサービス。"},
    {"category": "AWSセキュリティ", "sort_order": 8, "term": "AWS Security Hub", "description": "複数のAWSセキュリティサービスの検出結果を一元集約し、セキュリティ体制を包括的に可視化するサービス。"},
    {"category": "AWSセキュリティ", "sort_order": 9, "term": "AWS Certificate Manager", "description": "SSL/TLS証明書のプロビジョニング・管理・デプロイを自動化するサービス。HTTPS通信の暗号化に使用する。"},
    {"category": "AWSセキュリティ", "sort_order": 10, "term": "AWS Secrets Manager", "description": "データベースパスワードやAPIキーなどのシークレットを安全に保存・ローテーション・取得するマネージドサービス。"},
    {"category": "AWSセキュリティ", "sort_order": 11, "term": "AWS Artifact", "description": "AWSのコンプライアンスレポートやセキュリティ認証ドキュメントを無料でダウンロードできるセルフサービスポータル。"},
    {"category": "AWSセキュリティ", "sort_order": 12, "term": "多要素認証（MFA）", "description": "パスワードに加えてデバイスや生体情報などの追加認証要素を組み合わせることで不正アクセスを防止するセキュリティ手法。"},
    {"category": "AWSセキュリティ", "sort_order": 13, "term": "最小権限の原則", "description": "ユーザーやシステムに対して業務に必要な最低限の権限のみを付与するセキュリティの基本原則。被害範囲を限定する。"},
    {"category": "AWSセキュリティ", "sort_order": 14, "term": "IAMポリシー", "description": "AWSリソースへのアクセス権限をJSON形式で定義するルール。誰がどのリソースにどの操作を許可/拒否するかを記述する。"},
    {"category": "AWSセキュリティ", "sort_order": 15, "term": "AWS Organizations", "description": "複数のAWSアカウントを一元管理するサービス。SCPによるアクセス制御や一括請求でガバナンスとコスト管理を実現する。"},
    # =========================================================================
    # AWS管理・ガバナンス（12語）
    # =========================================================================
    {"category": "AWS管理・ガバナンス", "sort_order": 1, "term": "Amazon CloudWatch", "description": "AWSリソースやアプリケーションのメトリクス・ログを監視するモニタリングサービス。アラーム設定で異常を通知できる。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 2, "term": "AWS CloudTrail", "description": "AWSアカウント内のAPI呼び出しを記録する監査ログサービス。誰がいつ何を操作したかを追跡できる。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 3, "term": "AWS CloudFormation", "description": "インフラをテンプレートコードで定義し、AWSリソースのプロビジョニングを自動化するIaCサービス。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 4, "term": "AWS Config", "description": "AWSリソースの構成変更を継続的に記録・評価するサービス。コンプライアンスルールへの準拠状況を自動チェックする。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 5, "term": "AWS Systems Manager", "description": "EC2インスタンスやオンプレミスサーバーを一元管理する運用サービス。パッチ適用・コマンド実行・パラメータ管理などを提供する。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 6, "term": "AWS Trusted Advisor", "description": "AWSのベストプラクティスに基づきコスト・パフォーマンス・セキュリティ・耐障害性・サービス制限を自動評価する推奨サービス。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 7, "term": "AWS Health Dashboard", "description": "AWSサービスの稼働状況とアカウントに影響するイベントをリアルタイムで確認できるダッシュボード。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 8, "term": "AWS Control Tower", "description": "マルチアカウント環境のセットアップとガバナンスを自動化するサービス。ランディングゾーンやガードレールを提供する。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 9, "term": "AWS CDK", "description": "TypeScriptやPythonなどのプログラミング言語でAWSインフラを定義できるフレームワーク。CloudFormationテンプレートを生成する。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 10, "term": "Amazon EventBridge", "description": "イベント駆動型アーキテクチャを構築するサーバーレスイベントバスサービス。AWSサービスやSaaSのイベントをルーティングする。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 11, "term": "AWS X-Ray", "description": "分散アプリケーションのリクエストをトレースし、パフォーマンスボトルネックやエラーの原因を特定するデバッグサービス。"},
    {"category": "AWS管理・ガバナンス", "sort_order": 12, "term": "AWS CLI", "description": "コマンドラインからAWSサービスを操作するためのツール。スクリプトによる自動化やリソース管理に使用される。"},
    # =========================================================================
    # AWS料金・サポート（10語）
    # =========================================================================
    {"category": "AWS料金・サポート", "sort_order": 1, "term": "AWS Cost Explorer", "description": "AWSの利用料金を可視化・分析するサービス。過去のコストデータをグラフ表示し、将来の費用を予測できる。"},
    {"category": "AWS料金・サポート", "sort_order": 2, "term": "AWS Budgets", "description": "AWSの利用料金や使用量に対して予算を設定し、閾値超過時にアラート通知するコスト管理サービス。"},
    {"category": "AWS料金・サポート", "sort_order": 3, "term": "AWS料金計算ツール", "description": "AWSサービスの利用料金を事前に見積もるためのオンラインツール。構成を入力すると月額概算費用を算出できる。"},
    {"category": "AWS料金・サポート", "sort_order": 4, "term": "リザーブドインスタンス", "description": "1年または3年の利用コミットメントと引き換えに、オンデマンド料金から最大72%の割引を受けられる料金オプション。"},
    {"category": "AWS料金・サポート", "sort_order": 5, "term": "Savings Plans", "description": "一定の使用量をコミットすることで、EC2やLambdaなどのコンピューティング料金を最大72%割引する柔軟な料金モデル。"},
    {"category": "AWS料金・サポート", "sort_order": 6, "term": "スポットインスタンス", "description": "AWSの余剰キャパシティを最大90%割引で利用できるEC2インスタンス。中断の可能性があるが大幅にコストを削減できる。"},
    {"category": "AWS料金・サポート", "sort_order": 7, "term": "AWS無料利用枠", "description": "AWSの多くのサービスを一定範囲内で無料利用できるプログラム。12ヶ月無料枠・常時無料枠・トライアル枠の3種類がある。"},
    {"category": "AWS料金・サポート", "sort_order": 8, "term": "AWSサポートプラン", "description": "Basic・Developer・Business・Enterpriseの4段階のサポートプラン。上位プランほど応答時間が短くTAMが付く。"},
    {"category": "AWS料金・サポート", "sort_order": 9, "term": "AWS Billing Dashboard", "description": "AWSアカウントの請求情報を確認するダッシュボード。当月の利用料金や過去の請求履歴を一覧で確認できる。"},
    {"category": "AWS料金・サポート", "sort_order": 10, "term": "一括請求（Consolidated Billing）", "description": "AWS Organizationsで複数アカウントの利用料金を一つの請求にまとめる機能。ボリュームディスカウントの恩恵を受けられる。"},
    # =========================================================================
    # AI・ML基礎（20語）
    # =========================================================================
    {"category": "AI・ML基礎", "sort_order": 1, "term": "人工知能（AI）", "description": "人間の知的活動（学習・推論・判断など）をコンピュータで再現する技術の総称。機械学習や深層学習を包含する上位概念。"},
    {"category": "AI・ML基礎", "sort_order": 2, "term": "機械学習", "description": "データからパターンやルールを自動的に学習し、予測や分類を行うAIの中核技術。教師あり・教師なし・強化学習の3種類に大別される。"},
    {"category": "AI・ML基礎", "sort_order": 3, "term": "教師あり学習", "description": "入力データと正解ラベルのペアからモデルを学習させる手法。分類（スパム判定など）や回帰（価格予測など）に使用される。"},
    {"category": "AI・ML基礎", "sort_order": 4, "term": "教師なし学習", "description": "正解ラベルなしのデータから構造やパターンを発見する手法。クラスタリングや次元削減、異常検知などに使用される。"},
    {"category": "AI・ML基礎", "sort_order": 5, "term": "強化学習", "description": "エージェントが環境との相互作用を通じて報酬を最大化する行動方策を学習する手法。ゲームAIやロボティクスに活用される。"},
    {"category": "AI・ML基礎", "sort_order": 6, "term": "ニューラルネットワーク", "description": "人間の脳の神経回路を模倣した計算モデル。入力層・隠れ層・出力層で構成され、パターン認識や予測タスクに優れる。"},
    {"category": "AI・ML基礎", "sort_order": 7, "term": "深層学習（ディープラーニング）", "description": "多層のニューラルネットワークを用いた機械学習手法。画像認識・音声認識・自然言語処理で従来手法を大幅に上回る性能を実現する。"},
    {"category": "AI・ML基礎", "sort_order": 8, "term": "特徴量エンジニアリング", "description": "機械学習モデルに入力するデータの特徴を選択・変換・生成する工程。モデル精度に大きく影響する重要なプロセス。"},
    {"category": "AI・ML基礎", "sort_order": 9, "term": "過学習（オーバーフィッティング）", "description": "モデルが訓練データに過度に適合し、未知データへの汎化性能が低下する現象。正則化やドロップアウトで対策する。"},
    {"category": "AI・ML基礎", "sort_order": 10, "term": "バイアスとバリアンス", "description": "モデルの予測誤差を構成する2要素。バイアスが高いと未学習、バリアンスが高いと過学習となりトレードオフの関係にある。"},
    {"category": "AI・ML基礎", "sort_order": 11, "term": "推論（Inference）", "description": "学習済みモデルに新しいデータを入力して予測結果を得るプロセス。リアルタイム推論とバッチ推論の2形態がある。"},
    {"category": "AI・ML基礎", "sort_order": 12, "term": "訓練データ・検証データ・テストデータ", "description": "データセットを3分割して使う手法。訓練データでモデル学習、検証データでパラメータ調整、テストデータで最終評価を行う。"},
    {"category": "AI・ML基礎", "sort_order": 13, "term": "自然言語処理（NLP）", "description": "コンピュータが人間の言語を理解・生成・翻訳する技術領域。テキスト分類、感情分析、機械翻訳、質問応答などを含む。"},
    {"category": "AI・ML基礎", "sort_order": 14, "term": "コンピュータビジョン", "description": "コンピュータが画像や動画を解析・理解する技術領域。物体検出、顔認識、画像分類、セグメンテーションなどを含む。"},
    {"category": "AI・ML基礎", "sort_order": 15, "term": "回帰分析", "description": "入力変数と連続的な出力変数の関係をモデル化する統計手法。売上予測や気温予測など数値予測タスクに使用される。"},
    {"category": "AI・ML基礎", "sort_order": 16, "term": "分類（Classification）", "description": "データを事前定義されたカテゴリに振り分ける機械学習タスク。スパム検出、画像認識、疾病診断などに応用される。"},
    {"category": "AI・ML基礎", "sort_order": 17, "term": "クラスタリング", "description": "ラベルなしデータを類似度に基づいてグループに分類する教師なし学習手法。顧客セグメンテーションなどに使用される。"},
    {"category": "AI・ML基礎", "sort_order": 18, "term": "転移学習", "description": "あるタスクで学習済みのモデルの知識を、別の関連タスクに再利用する手法。少量データでも高精度モデルを構築できる。"},
    {"category": "AI・ML基礎", "sort_order": 19, "term": "データ前処理", "description": "機械学習モデルに入力する前にデータのクリーニング・正規化・欠損値処理・エンコーディングを行う準備工程。"},
    {"category": "AI・ML基礎", "sort_order": 20, "term": "モデル評価指標", "description": "モデルの性能を数値化する尺度。精度（Accuracy）、適合率（Precision）、再現率（Recall）、F1スコア、AUCなどがある。"},
    {"category": "AI・ML基礎", "sort_order": 21, "term": "異常検知", "description": "正常データのパターンから逸脱するデータポイントを検出する機械学習手法。不正取引検知やシステム障害予測に活用される。"},
    {"category": "AI・ML基礎", "sort_order": 22, "term": "次元削減", "description": "高次元データを情報を保持しながら低次元に変換する手法。PCAやt-SNEが代表的で、可視化や計算効率向上に使用される。"},
    {"category": "AI・ML基礎", "sort_order": 23, "term": "アンサンブル学習", "description": "複数の機械学習モデルを組み合わせて予測精度を向上させる手法。ランダムフォレストやXGBoostなどが代表的。"},
    {"category": "AI・ML基礎", "sort_order": 24, "term": "ハイパーパラメータチューニング", "description": "モデルの学習率やバッチサイズなど、事前に設定するパラメータを最適化する工程。グリッドサーチやベイズ最適化で実施する。"},
    # =========================================================================
    # 生成AI・基盤モデル（20語）
    # =========================================================================
    {"category": "生成AI・基盤モデル", "sort_order": 1, "term": "生成AI（Generative AI）", "description": "テキスト・画像・音声・コードなどの新しいコンテンツを生成できるAI技術。大規模言語モデルや拡散モデルが代表的手法。"},
    {"category": "生成AI・基盤モデル", "sort_order": 2, "term": "基盤モデル（Foundation Model）", "description": "大量のデータで事前学習された大規模AIモデル。様々なタスクに適応可能で、ファインチューニングやプロンプト指示で利用する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 3, "term": "大規模言語モデル（LLM）", "description": "数十億〜数兆パラメータを持つ言語生成モデル。大量テキストで学習し、文章生成・要約・翻訳・質問応答など多様な言語タスクを処理する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 4, "term": "Transformer", "description": "自己注意機構（Self-Attention）を用いたニューラルネットワークアーキテクチャ。GPTやBERTなど現代のLLMの基盤となる技術。"},
    {"category": "生成AI・基盤モデル", "sort_order": 5, "term": "トークン", "description": "LLMがテキストを処理する際の最小単位。単語や部分文字列に分割され、モデルの入出力やコスト計算の基本単位となる。"},
    {"category": "生成AI・基盤モデル", "sort_order": 6, "term": "プロンプトエンジニアリング", "description": "LLMから望ましい出力を得るために入力プロンプトを設計・最適化する技術。Zero-shot、Few-shot、Chain-of-Thoughtなどの手法がある。"},
    {"category": "生成AI・基盤モデル", "sort_order": 7, "term": "ファインチューニング", "description": "事前学習済みモデルを特定のタスクやドメインのデータで追加学習し、専門性を高める手法。少量データで高精度を実現する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 8, "term": "RAG（検索拡張生成）", "description": "外部知識ベースから関連情報を検索し、その情報をコンテキストとしてLLMに与えて回答を生成する手法。ハルシネーションを低減する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 9, "term": "エンベディング（埋め込み表現）", "description": "テキストや画像を数値ベクトルに変換する手法。意味的に近いデータが近いベクトル空間に配置され、類似検索に活用される。"},
    {"category": "生成AI・基盤モデル", "sort_order": 10, "term": "ハルシネーション", "description": "LLMが事実に基づかない情報をもっともらしく生成してしまう現象。RAGやグラウンディングなどの手法で軽減を図る。"},
    {"category": "生成AI・基盤モデル", "sort_order": 11, "term": "Temperature", "description": "LLMの出力のランダム性を制御するパラメータ。低い値で決定論的な出力、高い値で多様性のある出力を生成する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 12, "term": "RLHF（人間フィードバック強化学習）", "description": "人間の評価フィードバックを報酬シグナルとしてLLMを強化学習で調整する手法。有害出力の抑制や品質向上に使用される。"},
    {"category": "生成AI・基盤モデル", "sort_order": 13, "term": "マルチモーダルAI", "description": "テキスト・画像・音声・動画など複数の入力形式を同時に処理・理解できるAIモデル。GPT-4VやClaude 3が代表例。"},
    {"category": "生成AI・基盤モデル", "sort_order": 14, "term": "プロンプトテンプレート", "description": "LLMへの入力を構造化するための再利用可能なプロンプトの雛形。変数部分を埋めることで一貫した出力品質を確保する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 15, "term": "コンテキストウィンドウ", "description": "LLMが一度に処理できるトークン数の上限。入力プロンプトと出力の合計がこの範囲内に収まる必要がある。"},
    {"category": "生成AI・基盤モデル", "sort_order": 16, "term": "Few-shotプロンプティング", "description": "プロンプト内に数例の入出力ペアを含めてLLMにタスクのパターンを示す手法。学習なしで新タスクに適応させられる。"},
    {"category": "生成AI・基盤モデル", "sort_order": 17, "term": "Chain-of-Thought推論", "description": "LLMに段階的な推論過程を明示させることで、複雑な問題の回答精度を向上させるプロンプト技法。"},
    {"category": "生成AI・基盤モデル", "sort_order": 18, "term": "モデルパラメータ", "description": "ニューラルネットワーク内の学習可能な重みの総数。パラメータ数が多いほどモデルの表現力が高く、計算コストも増大する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 19, "term": "蒸留（Distillation）", "description": "大規模な教師モデルの知識を小規模な生徒モデルに転写する手法。推論速度とコストを改善しつつ性能を維持する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 20, "term": "ベクトルデータベース", "description": "高次元ベクトルデータの保存と類似性検索に最適化されたデータベース。RAGの知識ベースやレコメンデーションに使用される。"},
    {"category": "生成AI・基盤モデル", "sort_order": 21, "term": "グラウンディング", "description": "LLMの出力を外部データソースや事実情報に基づかせる技術。ハルシネーションを防ぎ、回答の正確性と信頼性を向上させる。"},
    {"category": "生成AI・基盤モデル", "sort_order": 22, "term": "ガードレール（AI）", "description": "AIモデルの出力が安全性・倫理性・ポリシーの基準を満たすよう制約を設けるメカニズム。有害コンテンツの生成を防止する。"},
    {"category": "生成AI・基盤モデル", "sort_order": 23, "term": "AIエージェント", "description": "LLMが自律的にツール利用・計画立案・タスク実行を行う仕組み。複雑な問題を段階的に解決するシステムを構築できる。"},
    {"category": "生成AI・基盤モデル", "sort_order": 24, "term": "量子化（Quantization）", "description": "モデルの重みパラメータのビット精度を下げてメモリ使用量と推論速度を改善する技術。精度と効率のトレードオフを管理する。"},
    # =========================================================================
    # AWS AIサービス（12語）
    # =========================================================================
    {"category": "AWS AIサービス", "sort_order": 1, "term": "Amazon Bedrock", "description": "複数の基盤モデル（Claude、Titan、Llama等）をAPI経由で利用できるフルマネージドサービス。カスタマイズやRAG構築も可能。"},
    {"category": "AWS AIサービス", "sort_order": 2, "term": "Amazon SageMaker", "description": "機械学習モデルの構築・学習・デプロイを統合的に行えるフルマネージドML開発プラットフォーム。ノートブックからエンドポイントまで対応。"},
    {"category": "AWS AIサービス", "sort_order": 3, "term": "Amazon Rekognition", "description": "画像・動画の分析を行うAIサービス。顔検出・物体認識・テキスト抽出・コンテンツモデレーションなどを提供する。"},
    {"category": "AWS AIサービス", "sort_order": 4, "term": "Amazon Comprehend", "description": "テキストから感情・エンティティ・キーフレーズ・言語を自動抽出する自然言語処理サービス。文書分類にも対応する。"},
    {"category": "AWS AIサービス", "sort_order": 5, "term": "Amazon Translate", "description": "ニューラル機械翻訳を提供するAWSサービス。75以上の言語間のリアルタイム翻訳やバッチ翻訳に対応する。"},
    {"category": "AWS AIサービス", "sort_order": 6, "term": "Amazon Textract", "description": "文書画像からテキスト・テーブル・フォームデータを自動抽出するOCRサービス。手書き文字やPDFにも対応する。"},
    {"category": "AWS AIサービス", "sort_order": 7, "term": "Amazon Polly", "description": "テキストを自然な音声に変換するText-to-Speechサービス。多言語・多話者対応でリアルタイム音声合成が可能。"},
    {"category": "AWS AIサービス", "sort_order": 8, "term": "Amazon Transcribe", "description": "音声をテキストに変換する自動音声認識（ASR）サービス。リアルタイム文字起こしやバッチ処理に対応する。"},
    {"category": "AWS AIサービス", "sort_order": 9, "term": "Amazon Personalize", "description": "パーソナライズされたレコメンデーションをリアルタイムで生成するMLサービス。ECサイトの商品推薦などに活用される。"},
    {"category": "AWS AIサービス", "sort_order": 10, "term": "Amazon Forecast", "description": "時系列データから将来の需要や数値を予測するフルマネージドMLサービス。在庫計画や売上予測に活用される。"},
    {"category": "AWS AIサービス", "sort_order": 11, "term": "Amazon Kendra", "description": "機械学習を活用したインテリジェント検索サービス。自然言語の質問に対して文書から正確な回答を返す。"},
    {"category": "AWS AIサービス", "sort_order": 12, "term": "Amazon Q", "description": "AWSが提供する生成AI搭載のアシスタントサービス。ビジネスデータに基づく質問応答やコード生成を支援する。"},
    {"category": "AWS AIサービス", "sort_order": 13, "term": "Amazon Lex", "description": "会話型AIインターフェースを構築するサービス。音声やテキストによるチャットボットやIVRシステムを開発できる。"},
    {"category": "AWS AIサービス", "sort_order": 14, "term": "Amazon Titan", "description": "AWS独自の基盤モデルファミリー。テキスト生成・エンベディング・画像生成など複数モデルをBedrock経由で利用できる。"},
    {"category": "AWS AIサービス", "sort_order": 15, "term": "SageMaker Studio", "description": "機械学習の開発・学習・デプロイを統合的に行えるWeb IDEベースの開発環境。JupyterLabベースで協調作業に対応する。"},
    {"category": "AWS AIサービス", "sort_order": 16, "term": "Amazon CodeWhisperer", "description": "AIによるコード補完・生成サービス。開発者のコメントやコードコンテキストに基づきリアルタイムでコード候補を提示する。"},
    # =========================================================================
    # 責任あるAI（10語）
    # =========================================================================
    {"category": "責任あるAI", "sort_order": 1, "term": "バイアス検出", "description": "AIモデルの学習データや予測結果に含まれる偏り（性別・人種・年齢等による不公平な傾向）を検出する技術・プロセス。"},
    {"category": "責任あるAI", "sort_order": 2, "term": "説明可能性（XAI）", "description": "AIモデルの予測根拠や意思決定過程を人間が理解できる形で提示する技術。SHAP値やLIMEなどの手法がある。"},
    {"category": "責任あるAI", "sort_order": 3, "term": "公平性（Fairness）", "description": "AIシステムが特定のグループに対して不当に有利・不利な結果を出さないこと。統計的パリティや機会均等などの指標で評価する。"},
    {"category": "責任あるAI", "sort_order": 4, "term": "透明性（Transparency）", "description": "AIシステムの仕組み・学習データ・意思決定プロセスを利害関係者に開示すること。信頼構築とアカウンタビリティの基盤となる。"},
    {"category": "責任あるAI", "sort_order": 5, "term": "Human-in-the-Loop", "description": "AIの判断プロセスに人間の監視・確認・介入を組み込む設計パターン。重要な意思決定での安全性と品質を担保する。"},
    {"category": "責任あるAI", "sort_order": 6, "term": "AIガバナンス", "description": "組織におけるAIの開発・運用に関するポリシー・プロセス・体制を定めるフレームワーク。リスク管理と法令遵守を確保する。"},
    {"category": "責任あるAI", "sort_order": 7, "term": "SageMaker Clarify", "description": "SageMakerの機能で、MLモデルのバイアス検出と説明可能性分析を行う。学習前・学習後のバイアスメトリクスを提供する。"},
    {"category": "責任あるAI", "sort_order": 8, "term": "AI倫理", "description": "AIの開発・利用における道徳的原則と行動規範。プライバシー保護、差別防止、人間の自律性尊重などの価値を追求する。"},
    {"category": "責任あるAI", "sort_order": 9, "term": "モデルカード", "description": "MLモデルの性能・制限事項・意図された使用目的・倫理的考慮事項を文書化した標準化されたレポート形式。"},
    {"category": "責任あるAI", "sort_order": 10, "term": "データガバナンス", "description": "AI学習データの品質・プライバシー・セキュリティ・コンプライアンスを管理するための方針・プロセス・技術の体系。"},
    {"category": "責任あるAI", "sort_order": 11, "term": "差分プライバシー", "description": "個人データのプライバシーを数学的に保証しながら統計分析やモデル学習を可能にする技術。ノイズ付加により情報漏洩を防ぐ。"},
    {"category": "責任あるAI", "sort_order": 12, "term": "モデル監視（Model Monitoring）", "description": "デプロイ済みMLモデルの性能劣化やデータドリフトを継続的に監視し、品質低下を検出するプロセス。"},
    {"category": "責任あるAI", "sort_order": 13, "term": "AWS AI Service Cards", "description": "AWSのAIサービスに関する責任あるAI情報を文書化したもの。想定ユースケース・制限事項・ベストプラクティスを記載する。"},
    {"category": "責任あるAI", "sort_order": 14, "term": "毒性検出（Toxicity Detection）", "description": "テキストコンテンツに含まれる有害・攻撃的・不適切な表現を自動検出する技術。コンテンツモデレーションの基盤となる。"},
    {"category": "責任あるAI", "sort_order": 15, "term": "レッドチーミング（AI）", "description": "AIシステムの脆弱性や有害出力を意図的に引き出すテスト手法。プロンプトインジェクションや安全性の欠陥を事前に発見する。"},
]


def seed_glossary(db: Session) -> bool:
    """用語集の初期データを投入する。

    既存データがある場合でも、GLOSSARY_SEED_DATAに含まれるが
    DBに存在しない用語を追加する（差分投入）。

    Returns:
        True: 新規用語を投入した場合 / False: 追加なし（全て既存）
    """
    # 既存のterm名を取得
    existing_terms: set[str] = {
        row.term
        for row in db.query(GlossaryTermModel.term).all()
    }

    # GLOSSARY_SEED_DATAのうち、DBに存在しない用語のみ追加
    added = False
    for item in GLOSSARY_SEED_DATA:
        if item["term"] not in existing_terms:
            term = GlossaryTermModel(
                id=str(uuid.uuid4()),
                category=item["category"],
                sort_order=item["sort_order"],
                term=item["term"],
                description=item["description"],
            )
            db.add(term)
            added = True

    if added:
        db.commit()

    return added
