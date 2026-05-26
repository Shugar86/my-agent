import PlaygroundDemo from '../components/demo/PlaygroundDemo';
import PageHeader from '../components/ui/PageHeader';
import { t } from '../i18n';

/** In-app live demo — same playground as showcase, without leaving SPA. */
export default function DemoPage() {
  return (
    <div className="page-content">
      <PageHeader
        title={t('demoPage.title')}
        subtitle={t('demoPage.subtitle')}
      />
      <PlaygroundDemo showAdvancedPresets />
    </div>
  );
}
