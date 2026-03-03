export const TOOL_META: Record<string, { active: string; done: string }> = {
  execute_python: { active: 'Executing code', done: 'Executed code' },
  todo: { active: 'Updating task list', done: 'Updated task list' },
  list_sources: { active: 'Listing sources', done: 'Listed sources' },
  ask_question: { active: 'Asking for clarification', done: 'Asked for clarification' },
}

export const HIDDEN_TOOLS = new Set(['ask_question'])
