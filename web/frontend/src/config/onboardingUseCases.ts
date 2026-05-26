/** Onboarding vertical picker — ids and bundled fallback when showcase JSON unavailable. */

export const ONBOARDING_USECASE_IDS = ['ararat', 'pegasszn', 'pretenzia', 'my-agent'] as const;

export type OnboardingUsecaseId = (typeof ONBOARDING_USECASE_IDS)[number];

export const ONBOARDING_USECASE_TEMPLATES: Record<OnboardingUsecaseId, string> = {
  ararat: 'tpl_beauty_consultant',
  pegasszn: 'tpl_content_repurpose',
  pretenzia: 'tpl_lead_qualifier',
  'my-agent': 'tpl_competitor_intelligence',
};

export interface OnboardingUsecaseCard {
  id: OnboardingUsecaseId;
  vertical: string;
  title: string;
  one_liner: string;
  metric: string;
  persona: {
    snippets: Array<{ text: string }>;
  };
}

/** Minimal cards so step 2 never renders empty without network. */
export const ONBOARDING_USECASE_FALLBACK: OnboardingUsecaseCard[] = [
  {
    id: 'ararat',
    vertical: 'Ювелирный retail',
    title: 'Mary Jewelry — AI-консультант Мари',
    one_liner: 'Telegram-бот консультант с каталогом, RAG и записью на приём',
    metric: '4 persona · 1 API',
    persona: {
      snippets: [
        {
          text: 'Доброго дня! Меня зовут Мари. Помогу подобрать изделие Mary Jewelry — для себя или в подарок?',
        },
      ],
    },
  },
  {
    id: 'pegasszn',
    vertical: 'Travel / Tourism',
    title: 'PEGAS Touristik — автоканал',
    one_liner: 'AI ведёт Telegram-канал: посты, RAG по турам, комментинг',
    metric: '2 поста/день · 88 cron triggers',
    persona: {
      snippets: [
        {
          text: 'Представь: утро, кофе на балконе, и впереди — море без будильника. Турция, 7 ночей, всё включено.',
        },
      ],
    },
  },
  {
    id: 'pretenzia',
    vertical: 'Legal RU',
    title: 'Pretenzia — претензии для РФ',
    one_liner: '8 типов документов: форма → оплата → PDF на email',
    metric: '190 ₽ · Robokassa · 15 000+ docs',
    persona: {
      snippets: [
        {
          text: 'Претензия продавцу: требование возврата денежных средств за некачественный товар по ЗоЗПП.',
        },
      ],
    },
  },
  {
    id: 'my-agent',
    vertical: 'Workflow OS',
    title: 'My Agent — Competitor Intelligence',
    one_liner: 'Visual DAG builder + marketplace + multi-agent research за 90 сек',
    metric: '90 сек · $0.42 · DOCX brief',
    persona: {
      snippets: [
        {
          text: '2 parallel agents → SWOT → DOCX brief — замена ~4 часов competitive research.',
        },
      ],
    },
  },
];

export function filterOnboardingUsecaseCards<T extends { id: string }>(cards: T[]): T[] {
  return cards.filter((c) =>
    ONBOARDING_USECASE_IDS.includes(c.id as OnboardingUsecaseId),
  );
}
