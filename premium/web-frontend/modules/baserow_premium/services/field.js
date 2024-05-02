export default (client) => {
  return {
    generateAIFieldValues(fieldId, rowIds) {
      return client.post(
        `/database/fields/${fieldId}/generate-ai-field-values/`,
        { row_ids: rowIds }
      )
    },
    generateAIFormula(tableId, aiType, aiModel, prompt) {
      return client.post(
        `/database/fields/table/${tableId}/generate-ai-formula/`,
        {
          ai_type: aiType,
          ai_model: aiModel,
          ai_prompt: prompt,
        }
      )
    },
  }
}
