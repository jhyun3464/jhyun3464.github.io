---
layout: single
title: "OpenAI, ChatGPT 및 Codex CLI에 '스킬(Skills)' 기능 조용히 도입"
date: 2025-12-13T05:29:38.347620+00:00
categories: [Tech, Trends]
tags: ['OpenAI', 'Anthropic', 'Skills', 'LLM', 'AI Agent', 'ChatGPT', 'Codex CLI', 'Code Interpreter', 'Agentic AI Foundation', 'Standardization', 'Prompt Engineering', 'RAG', 'MCP', 'GPT-5.2']
author_profile: true
---

OpenAI가 Anthropic이 개척한 '스킬(Skills)' 메커니즘을 ChatGPT와 Codex CLI에 조용히 도입하고 있습니다. 스킬은 단순히 마크다운 파일과 선택적인 리소스 및 스크립트로 구성된 폴더이며, 파일 시스템 탐색 및 읽기 기능을 갖춘 LLM 도구라면 사용할 수 있도록 설계되었습니다.

**ChatGPT의 스킬 구현:**
ChatGPT의 코드 인터프리터 기능 내부에 새로운 `/home/oai/skills` 폴더가 발견되었습니다. 이 폴더는 프롬프트를 통해 접근하고 내용을 탐색할 수 있습니다. 현재 스프레드시트, docx, PDF 처리 스킬이 포함되어 있습니다. 특히 PDF 및 문서 처리 방식은 흥미로운데, 텍스트 추출 시 손실될 수 있는 레이아웃 및 그래픽 정보를 유지하기 위해 문서를 페이지별 PNG 이미지로 렌더링한 다음 비전-활성화된 GPT 모델(예: GPT-4V 또는 그 이후 모델)에 전달하는 방식을 사용합니다.

시연 사례로, '현재 리무 나무 상황과 카카포 번식기에 미치는 영향에 대한 PDF 요약본 생성' 프롬프트에 GPT-5.2 모델이 응답했습니다. 모델은 'PDF 생성 지침을 위해 skill.md 읽기'와 '리무 나무와 카카포 2025 번식 상태 검색'과 같은 내부 과정을 명시적으로 언급하며 작업을 수행했습니다. 약 11분이 소요되었으며, PDF 렌더링 중 카카포(Kākāpō)의 장음 표기(macron)가 지원되지 않는 글꼴 문제를 인지하고 다른 글꼴로 전환하는 등 자율적인 작업 개선 능력을 보였습니다.

**Codex CLI의 스킬 구현:**
약 2주 전, OpenAI의 오픈소스 Codex CLI 도구에는 'feat: experimental support for skills.md'라는 PR이 병합되어 스킬에 대한 실험적 지원이 추가되었습니다. 문서에 따르면 `~/.codex/skills` 폴더 내의 모든 폴더가 스킬로 취급됩니다. 사용자는 `--enable skills` 옵션을 사용하여 Codex CLI를 실행해야 합니다.

예시로, Claude Opus 4.5를 사용하여 Datasette 플러그인 생성 스킬을 작성하고, 이를 `~/.codex/skills/datasette-plugin` 경로에 설치했습니다. 이후 Codex CLI에 '이 폴더에 PyPI의 cowsay를 사용하여 `/cowsay?text=hello` 페이지를 추가하는 Datasette 플러그인을 작성해 달라'고 프롬프트하자 완벽하게 작동하는 코드를 생성했습니다. 이는 LLM이 외부 도구와 상호작용하고 코드를 생성하는 강력한 에이전트 기능을 보여줍니다.

**시사점:**
작성자는 Anthropic의 스킬이 MCP(Multi-Modal Context Protocol)보다 더 중요하다고 평가했던 자신의 예측이 맞았음을 강조합니다. 스킬은 매우 가벼운 사양을 기반으로 하지만, 향후 Agentic AI Foundation(AAIF)과 같은 기관에서 공식적으로 문서화하여 표준화할 필요성이 제기되고 있습니다. 이는 LLM의 에이전트 능력 확장에 있어 핵심적인 트렌드이며, 다양한 LLM 플랫폼 간의 상호 운용성 및 기능 확장의 기반이 될 것으로 예상됩니다.

### 💬 개발자 반응 (Comments)
개발자들은 Anthropic이 '너무 간단해서 명백해 보이는' 혁신(MCP, 스킬)을 계속 내놓고 OpenAI가 이를 따라잡는 모습에 주목했습니다. 여러 개발자들이 '스킬'의 개념에 대해 토론하며, 본질적으로는 **'콘텍스트 관리 도구'** 또는 **'사용자 및 시스템 프롬프트 스터핑을 컨텍스트에 자동으로 도입하는 방법'**으로 이해했습니다. 이는 기존의 AI 래퍼 앱이 하던 체계적인 프롬프트 스터핑, RAG, MCP 등의 기능을 줄일 수 있는 방식이라고 분석했습니다.

스킬의 구현 방식에 대한 기술적인 질문도 있었는데, 특히 PDF 생성에 11분이라는 긴 시간이 걸린 이유(TeX, PDF 파일 사양, 프린트 드라이버 등)에 대한 궁금증을 표했습니다. 또한, OpenAI가 스킬을 벤더 특정 폴더(`~/.codex/`)에 저장하는 것에 대한 우려와 함께 Agentic AI Foundation(AAIF)이 `AGENTS.md`를 기여한 만큼, 스킬 또한 벤더 간의 **표준화**를 이루어야 한다는 강력한 요구가 있었습니다. 한 개발자는 이러한 표준화 노력에 발맞춰 어떤 LLM에서도 스킬을 사용할 수 있도록 하는 `open-skills`라는 오픈소스 프로젝트를 공유하며 커뮤니티의 관심을 나타냈습니다.

전반적으로, 개발자들은 스킬이 **MCP와 같은 '종합 선물 세트' 방식의 리소스와 맞춤형 스킬을 혼합하는 미래**를 만들 것이라고 예상했습니다. MCP가 서비스의 API 및 문서와 같은 '무엇을 할 수 있는지'에 대한 의미론적 정의를 제공한다면, 스킬은 이러한 서드파티 인터페이스와 맞춤형 코드를 결합하여 LLM/에이전트에 보다 컨텍스트 중심적인 기능을 제공할 것이라는 시각입니다. 이는 LLM의 에이전트 기능과 외부 도구 연동의 중요한 진전으로 평가되었습니다.

---
[원문 보러가기](https://simonwillison.net/2025/Dec/12/openai-skills/)
