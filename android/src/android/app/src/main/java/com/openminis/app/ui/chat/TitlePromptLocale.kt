package com.openminis.app.ui.chat

import java.util.Locale

/**
 * Shared system prompt for session title generation. Used by BOTH the auto
 * path (ChatViewModel.generateSessionTitleIfNeeded) and the manual Regenerate
 * path (SessionListViewModel.regenerateTitle) so the two never drift. Matches
 * iOS callSubModelForTitle's system prompt verbatim.
 *
 * Callers pass this as the bare `systemPrompt`; for OAuth Anthropic instances
 * AnthropicProvider.resolveSystemPrompt force-prepends the Claude Code prefix
 * block at the provider layer (and strips a caller-supplied one), so callers
 * do NOT need to prepend it themselves.
 */
internal const val TITLE_GEN_SYSTEM_PROMPT: String =
    "You generate concise titles for conversations. You MUST respond with a single valid JSON object: {\"title\": \"...\", \"category\": \"...\"}. No other text."

/**
 * Build the language directive appended to the title-generation
 * user prompt so the model produces a title in the user's UI language even
 * when the conversation contents are in another language.
 *
 * Resolution: `Locale.getDefault()` — the app does not currently expose an
 * in-app language override. If parsing the locale ever fails, falls back to
 * "en" / "English" rather than throwing, so title generation never breaks
 * over a malformed locale.
 */
internal fun titleLanguageDirective(locale: Locale = Locale.getDefault()): String {
    val (code, human) = resolveTitleLanguageCode(locale)
    return buildString {
        append("\n\n")
        append("The user's app interface language is \"").append(code)
            .append("\" (").append(human).append("). Generate the title primarily in this language. ")
        append("If the conversation content is in a different language, you may keep proper nouns ")
        append("from it, but the overall title language should match the interface language.\n")
    }
}

private fun resolveTitleLanguageCode(locale: Locale): Pair<String, String> {
    return try {
        val lang = locale.language.takeIf { it.isNotEmpty() } ?: return "en" to "English"
        val human = humanReadable[lang] ?: locale.getDisplayLanguage(Locale.ENGLISH)
            .ifEmpty { lang }
        lang to human
    } catch (_: Exception) {
        "en" to "English"
    }
}

private val humanReadable: Map<String, String> = mapOf(
    "en" to "English",
    "ja" to "日本語 / Japanese",
    "ko" to "한국어 / Korean",
    "fr" to "Français / French",
    "de" to "Deutsch / German",
    "es" to "Español / Spanish",
    "it" to "Italiano / Italian",
    "pt" to "Português / Portuguese",
    "ru" to "Русский / Russian",
    "ar" to "العربية / Arabic",
    "hi" to "हिन्दी / Hindi",
    "vi" to "Tiếng Việt / Vietnamese",
    "th" to "ไทย / Thai",
    "id" to "Bahasa Indonesia / Indonesian",
    "tr" to "Türkçe / Turkish",
    "nl" to "Nederlands / Dutch",
    "pl" to "Polski / Polish",
)
