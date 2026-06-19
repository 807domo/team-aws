# Requirements Document

## Introduction

愛媛探索AIクイズ（Ehime Exploration AI Quiz）は、愛媛県の大学生・高専生が愛媛の魅力を再発見しながら、AWS/AIのITスキルを自然に習得できる学習プラットフォームである。愛媛の観光・名所・郷土料理をテーマにしたクイズを通じて、抽象的なクラウド/AI概念を親しみやすい形で学習できる。ステージは中予・南予・東予の地域別に設定される。

## Glossary

- **Quiz_System**: クイズの出題・採点・結果表示を行うコアシステム
- **Explanation_Engine**: クイズ回答後にAI/AWSの解説と愛媛トリビアを生成・表示するコンポーネント
- **User_Record_Store**: ユーザーの正答率・学習ログ・成績を保存するデータストア
- **Course**: 愛媛の地域・テーマに基づいたクイズのグループ（例：「松山城コース（基礎）」「しまなみ海道コース（上級）」）
- **Mock_Exam_Engine**: AWS認定資格模擬試験モードを提供するコンポーネント
- **AI_Question_Generator**: 誤答分析に基づき「愛媛×AWS」のパーソナライズ問題を自動生成するAIコンポーネント
- **Results_Dashboard**: レーダーチャートとスコアでIT知識レベルと愛媛探索率を可視化する画面
- **User**: 愛媛県内の大学生・高専生（プログラミング未経験者・文系含む）

## Requirements

### Requirement 1: コース選択画面の表示

**User Story:** As a User, I want to see available quiz courses organized by Ehime region and difficulty, so that I can choose a learning path that interests me.

#### Acceptance Criteria

1. WHEN the User opens the application, THE Quiz_System SHALL display a course selection screen with available courses grouped by region (中予, 南予, 東予)
2. THE Quiz_System SHALL display each Course with its name, region, and difficulty level (基礎, 中級, 上級)
3. WHEN the User selects a Course, THE Quiz_System SHALL navigate to the quiz screen for that Course
4. THE Quiz_System SHALL always guarantee at least one Course per region (中予, 南予, 東予) so that all regions are represented at all times
5. IF the system is in an initialization state where no Courses have been loaded for any region, THEN THE Quiz_System SHALL display all regions as "準備中" (coming soon) and disable selection until courses are available

### Requirement 2: クイズ出題と回答

**User Story:** As a User, I want to answer 4-choice quizzes about Ehime tourism and landmarks, so that I can learn about my region while studying IT concepts.

#### Acceptance Criteria

1. WHEN a Course is started, THE Quiz_System SHALL present quiz questions in a 4-choice format with exactly one correct answer
2. THE Quiz_System SHALL present questions themed around Ehime tourism, landmarks, and local cuisine, each incorporating an AWS or AI concept
3. WHEN the User selects an answer, THE Quiz_System SHALL always display whether the answer is correct or incorrect with visual feedback without exception, regardless of technical issues or rapid user interaction
4. THE Quiz_System SHALL present one question at a time before proceeding to the next question
5. WHEN the User has answered all questions in a Course, THE Quiz_System SHALL display a course completion summary showing the number of correct answers out of total questions

### Requirement 3: 解説画面の表示

**User Story:** As a User, I want to see explanations after answering each quiz question, so that I can understand the AWS/AI concepts behind the quiz content.

#### Acceptance Criteria

1. WHEN the User answers a question (correctly or incorrectly), THE Explanation_Engine SHALL display an explanation screen containing an Ehime-related trivia section and a corresponding AWS service or AI concept explanation section
2. THE Explanation_Engine SHALL generate explanations that explicitly name at least one AWS service or AI concept and describe its relationship to the Ehime topic of the question, using vocabulary accessible to programming beginners (no unexplained technical jargon)
3. THE Explanation_Engine SHALL display explanations between 100 and 500 characters in total length
4. WHEN the User taps the "次へ" (next) button on the explanation screen, THE Quiz_System SHALL proceed to the next question
5. IF the Explanation_Engine fails to generate an explanation within 10 seconds, THEN THE Explanation_Engine SHALL display the pre-authored explanation stored with the question data

### Requirement 4: 正答率の記録

**User Story:** As a User, I want my quiz accuracy rates to be recorded, so that I can track my learning progress over time.

#### Acceptance Criteria

1. WHEN the User answers a question, THE User_Record_Store SHALL record the answer result (correct or incorrect), the question identifier, the Course identifier, and a timestamp
2. WHEN the User answers a question, THE User_Record_Store SHALL recalculate and store the accuracy rate for that Course as the number of correct answers divided by the total number of answers attempted in that Course, expressed as a percentage rounded to one decimal place
3. WHEN the User answers a question, THE User_Record_Store SHALL recalculate and store the cumulative accuracy rate across all Courses as the total number of correct answers divided by the total number of answers attempted across all Courses, expressed as a percentage rounded to one decimal place
4. IF the User answers the same question again in a repeated attempt of a Course, THEN THE User_Record_Store SHALL include all attempts in the accuracy rate calculation
5. IF the User_Record_Store fails to record an answer result, THEN THE Quiz_System SHALL display an error message indicating the result was not saved and SHALL allow the User to retry the operation
6. WHEN the Results_Dashboard or AI_Question_Generator requests accuracy data for a User, THE User_Record_Store SHALL return the per-Course accuracy rates and the cumulative accuracy rate

### Requirement 5: 模擬試験モード

**User Story:** As a User, I want to take timed mock exams aligned with AWS Certified Cloud Practitioner / AI Practitioner formats, so that I can assess my readiness for certification.

#### Acceptance Criteria

1. WHEN the User selects mock exam mode, THE Mock_Exam_Engine SHALL present the User with a choice between AWS Certified Cloud Practitioner exam (65 questions, 90 minutes) and AWS AI Practitioner exam (65 questions, 90 minutes) before starting the exam
2. WHILE the mock exam is in progress, THE Mock_Exam_Engine SHALL display a countdown timer showing remaining time in minutes and seconds
3. WHEN the timer expires, THE Mock_Exam_Engine SHALL end the exam. WHEN the User completes all questions, THE Mock_Exam_Engine SHALL end the exam. THE Mock_Exam_Engine SHALL mark unanswered questions as incorrect, calculate the score as a percentage, and assign a grade (A–E), and these steps MAY occur independently of each other
4. THE Mock_Exam_Engine SHALL present questions in 4-choice format that combine Ehime regional knowledge with AWS/AI certification topics corresponding to the selected exam type
5. IF the User attempts to navigate away during a mock exam, THEN THE Mock_Exam_Engine SHALL display a confirmation dialog warning that progress will be lost
6. WHILE the mock exam is in progress, THE Mock_Exam_Engine SHALL allow the User to navigate between questions and skip unanswered questions before final submission

### Requirement 6: 結果画面と成長可視化

**User Story:** As a User, I want to see my learning results visualized with charts and grades, so that I can understand my IT knowledge level and Ehime exploration progress.

#### Acceptance Criteria

1. WHEN the User completes a quiz or mock exam, THE Results_Dashboard SHALL display the score as a percentage (0–100%) and a grade determined by the following thresholds: A (90–100%), B (80–89%), C (70–79%), D (60–69%), E (0–59%)
2. WHEN the User views the Results_Dashboard, THE Results_Dashboard SHALL display a radar chart with one axis per AWS certification domain area (Cloud Concepts, Security, Technology, Billing for Cloud Practitioner; corresponding domains for AI Practitioner) where each axis value represents the User's accuracy rate (0–100%) for questions in that domain
3. WHEN the User views the Results_Dashboard, THE Results_Dashboard SHALL display the Ehime exploration rate as the percentage of completed Courses out of total available Courses, and the count of regions (中予, 南予, 東予) in which at least one Course has been completed
4. WHEN the User views the Results_Dashboard and at least 2 previous quiz or mock exam attempts exist, THE Results_Dashboard SHALL display the User's accuracy rate for each attempt in chronological order to show improvement trends
5. IF the User views the Results_Dashboard with no previous attempts recorded, THEN THE Results_Dashboard SHALL display a message indicating that no learning history is available yet

### Requirement 7: AWS資格出題傾向への対応

**User Story:** As a User, I want quiz questions that reflect actual AWS certification exam trends arranged with Ehime flavor, so that my studying directly prepares me for certification.

#### Acceptance Criteria

1. THE Quiz_System SHALL include questions covering each AWS Certified Cloud Practitioner (CLF-C02) exam domain: Cloud Concepts, Security and Compliance, Cloud Technology and Services, and Billing Pricing and Support, with a minimum of 3 questions per domain
2. THE Quiz_System SHALL include questions covering each AWS AI Practitioner (AIF-C01) exam domain: AI and ML Fundamentals, Generative AI, and Responsible AI, with a minimum of 3 questions per domain
3. THE Quiz_System SHALL associate each certification-aligned question with its corresponding exam domain label so that domain-level coverage can be verified
4. THE Quiz_System SHALL frame each certification question using an Ehime-related scenario (referencing Ehime geography, landmarks, local industry, or cuisine) while ensuring the question tests a specific AWS or AI concept identifiable without Ehime knowledge
5. IF a question's Ehime scenario is removed, THEN the underlying AWS or AI concept being tested SHALL remain identifiable from the question's answer choices and correct answer explanation

### Requirement 8: AIによるパーソナライズ問題生成

**User Story:** As a User, I want the system to analyze my incorrect answers and generate personalized questions targeting my weak areas, so that I can improve efficiently.

#### Acceptance Criteria

1. WHEN the User has accumulated 10 or more incorrect answers across all Courses combined, THE AI_Question_Generator SHALL analyze the incorrect answer patterns to identify weak topic areas, where a weak topic area is defined as any AWS/AI exam domain in which the User's incorrect answer rate is 50% or higher
2. WHEN weak areas are identified, THE AI_Question_Generator SHALL generate between 1 and 5 new quiz questions per identified weak topic area, combining Ehime regional information with the identified weak AWS/AI topics
3. THE AI_Question_Generator SHALL generate questions that follow the 4-choice format with exactly one correct answer, and include Ehime-themed context, an Ehime trivia explanation, and an AWS/AI concept explanation matching the structure defined in Requirement 9
4. IF the AI_Question_Generator fails to return a valid response within 30 seconds, or returns a response that does not contain exactly 4 choices with one correct answer, THEN THE Quiz_System SHALL fall back to presenting a pre-authored question from the question bank that targets the same weak topic area
5. WHEN a personalized question is generated, THE AI_Question_Generator SHALL associate the question with the relevant Course and difficulty level so that it appears in the User's quiz flow

### Requirement 9: クイズデータの管理

**User Story:** As a content administrator, I want quiz questions stored with their choices, correct answers, and explanations, so that the system can serve consistent quiz content.

#### Acceptance Criteria

1. THE Quiz_System SHALL store each question with its text, exactly four choices, exactly one correct answer indicator among the four choices, an Ehime trivia explanation, and an AWS/AI concept explanation
2. THE Quiz_System SHALL support a minimum of 30 quiz questions at launch, distributed across at least 3 Courses
3. THE Quiz_System SHALL associate each question with exactly one Course and one difficulty level selected from (基礎, 中級, 上級)
4. WHEN a question is retrieved, THE Quiz_System SHALL return the question text, four choices, correct answer indicator, Ehime trivia explanation, AWS/AI concept explanation, associated Course, and difficulty level
5. THE Quiz_System SHALL assign each question a unique identifier that distinguishes it from all other questions in the system
6. IF a question is submitted for storage with any required field empty or with a number of choices other than four, THEN THE Quiz_System SHALL reject the submission and indicate which fields are invalid
