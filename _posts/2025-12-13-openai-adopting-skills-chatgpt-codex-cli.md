---
layout: single
title: "OpenAI, ChatGPT 및 Codex CLI에 '스킬' 기능 조용히 도입"
date: 2025-12-13T06:54:07.657046+00:00
categories: [Tech, Trends]
tags: ['OpenAI', 'ChatGPT', 'Codex', 'LLM', 'AI Skills', 'Agentic AI', 'Prompt Engineering', 'Context Management', 'Anthropic', 'Standardization', 'CLI']
author_profile: true
---

![Header Image](/assets/images/2025-12-13-openai-adopting-skills-chatgpt-codex-cli.webp)

OpenAI가 자사의 ChatGPT 및 Codex CLI(명령줄 인터페이스)에 '스킬(skills)'이라는 새로운 기능을 조용히 도입하고 있다는 소식입니다. 이 기능은 특히 대규모 언어 모델(LLM)과의 상호작용 및 컨텍스트 관리에 있어 중요한 진전을 보여줍니다.

개발자 커뮤니티의 반응에 따르면, 이 '스킬' 기능은 본질적으로 컨텍스트 관리 도구로 작용합니다. 사용자의 질의에 따라 모델이 특정 '스킬'이 필요하다고 판단하면, 해당 스킬과 관련된 정의된 정보(스크립트, 문서 등)를 컨텍스트에 자동으로 주입하는 방식입니다. 이는 기술적으로 "프롬프트 스터핑(prompt stuffing)"의 자동화된 형태로 설명되며, 기존에 AI 래퍼(wrapper) 앱들이 수동으로 수행했던 체계적인 사용자 및 시스템 프롬프트 주입, RAG(검색 증강 생성), 그리고 Anthropic의 MCP(Multi-shot CoT Prompting)와 같은 기능을 상당 부분 대체하거나 통합할 수 있습니다.

많은 개발자들은 OpenAI의 이러한 움직임을 경쟁사인 Anthropic의 혁신(예: MCP, 그들만의 'Skills' 개념)을 따라잡는 것으로 보고 있습니다. Anthropic은 "너무 간단해서 명백해 보이는" 제품 혁신을 지속적으로 선보이며 업계에 영향을 미쳐왔고, OpenAI가 이를 벤치마킹하여 자사 제품에 유사한 기능을 "상식적으로 이해되는" 방식으로 통합하고 있다는 평가입니다.

기술적인 관점에서 '스킬'은 주로 마크다운(.md) 파일 형태로 정의되며, 이는 에이전트 기능을 위한 AGENTS.md와 유사한 방식입니다. 그러나 일부에서는 이러한 기능이 특정 벤더(OpenAI의 경우 .codex/ 폴더)에 종속되는 것에 대한 우려와 함께, Agentic AI Foundation(AAIF)과 같은 이니셔티브를 통해 이러한 에이전트 및 스킬 관련 기능이 업계 전반에 걸쳐 표준화되기를 희망하고 있습니다. 실제로, 다른 LLM에서도 '스킬'을 활용할 수 있도록 GitHub에서 'open-skills'라는 오픈소스 프로젝트가 공개되어 있으며, 이는 로컬 컨테이너에서 실행됩니다.

반면, 일부 개발자들은 AGENTS.md에 이어 또 다른 .md 파일을 통해 컨텍스트를 관리하는 방식이 전반적인 복잡성을 증가시키는 것은 아닌지에 대한 우려를 표명하기도 했습니다. 전반적으로 이 '스킬' 기능의 도입은 LLM 기반 애플리케이션 개발 방식과 컨텍스트 관리의 효율성에 큰 영향을 미칠 것으로 예상됩니다.

### 💬 개발자 반응 (Comments)
개발자들은 OpenAI의 '스킬' 도입에 대해 다양한 반응을 보였습니다:

*   **Anthropic과의 비교:** 많은 이들이 Anthropic이 MCP나 'Skills'와 같은 '간단하지만 명백한' 혁신을 먼저 선보였고, OpenAI가 이를 뒤따라가는 것으로 인지하고 있습니다. Anthropic의 디자인 사고 방식에 대한 관심도 높았습니다.
*   **기술적 이해:** '스킬'의 본질적인 메커니즘에 대한 질문이 많았으며, 대부분은 이를 '자동화된 프롬프트 스터핑' 또는 '컨텍스트 관리 도구'로 이해했습니다. AI 래퍼 앱의 필요성을 줄일 수 있다는 점에 주목했습니다.
*   **표준화 요구:** 벤더별 특정 폴더(예: `.codex/`)에 의존하는 방식에 대한 우려가 있었고, Agentic AI Foundation(AAIF) 및 AGENTS.md와 같은 노력을 통해 이러한 기능이 업계 전반에 걸쳐 표준화되기를 강력히 희망했습니다.
*   **복잡성 증가 우려:** 기존의 `agents.md`에 더해 새로운 `.md` 파일을 통한 컨텍스트 관리가 개발 복잡성을 가중시킬 수 있다는 의견도 있었습니다.
*   **커뮤니티 기여:** 다른 LLM에서도 '스킬'을 사용할 수 있게 해주는 'open-skills'라는 오픈소스 프로젝트가 언급되며 커뮤니티의 활발한 참여를 보여주었습니다.
*   **기타:** Simon Willison의 이미지 대체 텍스트 설정에 대한 감사의 표현과 함께, "OpenAI are" 대신 "OpenAI is"가 올바른 문법이라는 지적도 있었습니다.

---
[원문 보러가기](https://simonwillison.net/2025/Dec/12/openai-skills/)
