"""
問題バリデーターのユニットテスト
"""

import pytest

from app.domain.question_validator import ValidationResult, validate_question


def _valid_question_data() -> dict:
    """有効な問題データのベースを返す"""
    return {
        "id": "q-cc-001",
        "text": "松山城の別名は何でしょう？",
        "choice_1": "金亀城",
        "choice_2": "白鷺城",
        "choice_3": "烏城",
        "choice_4": "鶴ヶ城",
        "correct_choice_index": 0,
        "ehime_trivia": "松山城は加藤嘉明が築城した日本の現存12天守の一つです。",
        "aws_ai_explanation": "Amazon S3のバケット命名は城の別名のようにユニークである必要があります。",
        "course_id": "course-chuyo-basic",
        "difficulty": "基礎",
        "exam_domain": "Cloud Concepts",
    }


class TestValidateQuestion:
    """validate_question のテスト"""

    def test_valid_question_passes(self):
        """有効な問題データはバリデーションを通過する"""
        result = validate_question(_valid_question_data())
        assert result.is_valid is True
        assert result.errors == []

    def test_empty_text_fails(self):
        """空のテキストはバリデーション失敗"""
        data = _valid_question_data()
        data["text"] = ""
        result = validate_question(data)
        assert result.is_valid is False
        assert any("text" in e for e in result.errors)

    def test_missing_text_fails(self):
        """テキストフィールドがないとバリデーション失敗"""
        data = _valid_question_data()
        del data["text"]
        result = validate_question(data)
        assert result.is_valid is False
        assert any("text" in e for e in result.errors)

    def test_whitespace_only_text_fails(self):
        """空白のみのテキストはバリデーション失敗"""
        data = _valid_question_data()
        data["text"] = "   "
        result = validate_question(data)
        assert result.is_valid is False
        assert any("text" in e for e in result.errors)

    def test_empty_choice_fails(self):
        """空の選択肢はバリデーション失敗"""
        data = _valid_question_data()
        data["choice_2"] = ""
        result = validate_question(data)
        assert result.is_valid is False
        assert any("choice_2" in e for e in result.errors)

    def test_missing_choice_fails(self):
        """選択肢フィールドがないとバリデーション失敗"""
        data = _valid_question_data()
        del data["choice_3"]
        result = validate_question(data)
        assert result.is_valid is False
        assert any("choice_3" in e for e in result.errors)

    def test_correct_choice_index_out_of_range_fails(self):
        """correct_choice_index が範囲外だとバリデーション失敗"""
        data = _valid_question_data()
        data["correct_choice_index"] = 4
        result = validate_question(data)
        assert result.is_valid is False
        assert any("correct_choice_index" in e for e in result.errors)

    def test_correct_choice_index_negative_fails(self):
        """correct_choice_index が負の値だとバリデーション失敗"""
        data = _valid_question_data()
        data["correct_choice_index"] = -1
        result = validate_question(data)
        assert result.is_valid is False
        assert any("correct_choice_index" in e for e in result.errors)

    def test_correct_choice_index_missing_fails(self):
        """correct_choice_index がないとバリデーション失敗"""
        data = _valid_question_data()
        del data["correct_choice_index"]
        result = validate_question(data)
        assert result.is_valid is False
        assert any("correct_choice_index" in e for e in result.errors)

    def test_correct_choice_index_not_int_fails(self):
        """correct_choice_index が整数でないとバリデーション失敗"""
        data = _valid_question_data()
        data["correct_choice_index"] = "0"
        result = validate_question(data)
        assert result.is_valid is False
        assert any("correct_choice_index" in e for e in result.errors)

    def test_empty_ehime_trivia_fails(self):
        """空の ehime_trivia はバリデーション失敗"""
        data = _valid_question_data()
        data["ehime_trivia"] = ""
        result = validate_question(data)
        assert result.is_valid is False
        assert any("ehime_trivia" in e for e in result.errors)

    def test_empty_aws_ai_explanation_fails(self):
        """空の aws_ai_explanation はバリデーション失敗"""
        data = _valid_question_data()
        data["aws_ai_explanation"] = ""
        result = validate_question(data)
        assert result.is_valid is False
        assert any("aws_ai_explanation" in e for e in result.errors)

    def test_empty_course_id_fails(self):
        """空の course_id はバリデーション失敗"""
        data = _valid_question_data()
        data["course_id"] = ""
        result = validate_question(data)
        assert result.is_valid is False
        assert any("course_id" in e for e in result.errors)

    def test_invalid_difficulty_fails(self):
        """無効な difficulty はバリデーション失敗"""
        data = _valid_question_data()
        data["difficulty"] = "超上級"
        result = validate_question(data)
        assert result.is_valid is False
        assert any("difficulty" in e for e in result.errors)

    def test_missing_difficulty_fails(self):
        """difficulty がないとバリデーション失敗"""
        data = _valid_question_data()
        del data["difficulty"]
        result = validate_question(data)
        assert result.is_valid is False
        assert any("difficulty" in e for e in result.errors)

    @pytest.mark.parametrize("difficulty", ["基礎", "中級", "上級"])
    def test_valid_difficulties(self, difficulty: str):
        """有効な難易度はすべてバリデーション通過"""
        data = _valid_question_data()
        data["difficulty"] = difficulty
        result = validate_question(data)
        assert result.is_valid is True

    @pytest.mark.parametrize("index", [0, 1, 2, 3])
    def test_valid_choice_indices(self, index: int):
        """有効な correct_choice_index（0-3）はバリデーション通過"""
        data = _valid_question_data()
        data["correct_choice_index"] = index
        result = validate_question(data)
        assert result.is_valid is True

    def test_multiple_errors_reported(self):
        """複数のエラーが同時に報告される"""
        data = {
            "text": "",
            "choice_1": "",
            "choice_2": "選択肢2",
            "choice_3": "選択肢3",
            "choice_4": "選択肢4",
            "correct_choice_index": 5,
            "ehime_trivia": "",
            "aws_ai_explanation": "説明",
            "course_id": "",
            "difficulty": "無効",
        }
        result = validate_question(data)
        assert result.is_valid is False
        assert len(result.errors) >= 4

    # --- exam_domain バリデーションテスト ---

    @pytest.mark.parametrize(
        "domain",
        [
            "Cloud Concepts",
            "Security and Compliance",
            "Cloud Technology and Services",
            "Billing Pricing and Support",
            "AI and ML Fundamentals",
            "Generative AI",
            "Responsible AI",
        ],
    )
    def test_valid_exam_domains(self, domain: str):
        """有効な exam_domain 値はすべてバリデーション通過"""
        data = _valid_question_data()
        data["exam_domain"] = domain
        result = validate_question(data)
        assert result.is_valid is True

    def test_invalid_exam_domain_fails(self):
        """無効な exam_domain はバリデーション失敗"""
        data = _valid_question_data()
        data["exam_domain"] = "Invalid Domain"
        result = validate_question(data)
        assert result.is_valid is False
        assert any("exam_domain" in e for e in result.errors)

    def test_missing_exam_domain_fails(self):
        """exam_domain がないとバリデーション失敗"""
        data = _valid_question_data()
        del data["exam_domain"]
        result = validate_question(data)
        assert result.is_valid is False
        assert any("exam_domain" in e for e in result.errors)

    # --- id フィールド境界値テスト ---

    def test_empty_id_fails(self):
        """空の id はバリデーション失敗"""
        data = _valid_question_data()
        data["id"] = ""
        result = validate_question(data)
        assert result.is_valid is False
        assert any("id" in e for e in result.errors)

    def test_id_50_chars_passes(self):
        """50文字の id はバリデーション通過"""
        data = _valid_question_data()
        data["id"] = "a" * 50
        result = validate_question(data)
        assert result.is_valid is True

    def test_id_51_chars_fails(self):
        """51文字の id はバリデーション失敗"""
        data = _valid_question_data()
        data["id"] = "a" * 51
        result = validate_question(data)
        assert result.is_valid is False
        assert any("id" in e for e in result.errors)

    # --- ehime_trivia 文字数境界値テスト ---

    def test_ehime_trivia_200_chars_passes(self):
        """200文字の ehime_trivia はバリデーション通過"""
        data = _valid_question_data()
        data["ehime_trivia"] = "あ" * 200
        result = validate_question(data)
        assert result.is_valid is True

    def test_ehime_trivia_201_chars_fails(self):
        """201文字の ehime_trivia はバリデーション失敗"""
        data = _valid_question_data()
        data["ehime_trivia"] = "あ" * 201
        result = validate_question(data)
        assert result.is_valid is False
        assert any("ehime_trivia" in e for e in result.errors)

    # --- choice フィールド200文字境界値テスト ---

    def test_choice_200_chars_passes(self):
        """200文字の choice はバリデーション通過"""
        data = _valid_question_data()
        data["choice_1"] = "あ" * 200
        result = validate_question(data)
        assert result.is_valid is True

    def test_choice_201_chars_fails(self):
        """201文字の choice はバリデーション失敗"""
        data = _valid_question_data()
        data["choice_1"] = "あ" * 201
        result = validate_question(data)
        assert result.is_valid is False
        assert any("choice_1" in e for e in result.errors)


class TestValidationResult:
    """ValidationResult データクラスのテスト"""

    def test_default_errors_empty(self):
        """デフォルトの errors は空リスト"""
        result = ValidationResult(is_valid=True)
        assert result.errors == []

    def test_with_errors(self):
        """エラーリスト付きの結果"""
        errors = ["error1", "error2"]
        result = ValidationResult(is_valid=False, errors=errors)
        assert result.is_valid is False
        assert result.errors == errors
