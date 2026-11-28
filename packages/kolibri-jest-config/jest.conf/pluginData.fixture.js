const template = globalThis.document.createElement('template');
template.dataset.plugin = 'testmodule';
template.content.textContent = JSON.stringify({
  urls: {
    urls: {
      'kolibri:kolibri.plugins.learn:learnerclassroom_detail': [['api/classroom/%(id)s/', ['id']]],
      'kolibri:core:exam_detail': [['api/exam/%(id)s/', ['id']]],
      'kolibri:core:contentnode_list': [['api/content/contentnode/', []]],
      'kolibri:core:session_detail': [['api/session/%(id)s/', ['id']]],
    },
  },
});
globalThis.document.body.appendChild(template);
