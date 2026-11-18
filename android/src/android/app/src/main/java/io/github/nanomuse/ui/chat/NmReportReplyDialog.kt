package io.github.nanomuse.ui.chat

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.openminis.app.R
import io.github.nanomuse.cloud.NanoMuseCloud
import io.github.nanomuse.ui.home.MuseTones
import kotlinx.coroutines.launch

/** The five reasons a reply can be reported for, with the wire value the relay expects. */
enum class ReportReason(val wire: String, val label: Int) {
    HARMFUL("harmful", R.string.nm_report_reason_harmful),
    SEXUAL("sexual", R.string.nm_report_reason_sexual),
    HATE("hate", R.string.nm_report_reason_hate),
    WRONG("wrong", R.string.nm_report_reason_wrong),
    OTHER("other", R.string.nm_report_reason_other),
}

private const val NOTE_MAX = 500

/**
 * "Report this reply" (Play's AI-generated content policy): a reason, an optional note, Send.
 * With a FOMO Cloud account the report goes to the relay ([NanoMuseCloud.reportAiOutput]);
 * without one it opens the mail app addressed to the relay's support address. [text] is the
 * reply as the user saw it (its markdown source); [modelId] the model that wrote it, or empty.
 * Nothing in the chat changes either way; [onDone] closes the dialog.
 */
@Composable
fun NmReportReplyDialog(text: String, modelId: String, onDone: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var reason by remember { mutableStateOf<ReportReason?>(null) }
    var note by remember { mutableStateOf("") }
    var sending by remember { mutableStateOf(false) }
    val muted = MaterialTheme.colorScheme.onSurfaceVariant

    AlertDialog(
        onDismissRequest = { if (!sending) onDone() },
        title = { Text(stringResource(R.string.nm_report_reply_action)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text(stringResource(R.string.nm_report_reply_why), fontSize = 14.sp, color = muted)
                Spacer(Modifier.height(4.dp))
                ReportReason.values().forEach { r ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .selectable(selected = reason == r, enabled = !sending, role = Role.RadioButton) { reason = r }
                            .padding(vertical = 2.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(
                            selected = reason == r,
                            onClick = null,
                            enabled = !sending,
                            colors = RadioButtonDefaults.colors(selectedColor = MuseTones.action),
                        )
                        Spacer(Modifier.width(4.dp))
                        Text(stringResource(r.label), fontSize = 15.sp)
                    }
                }
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = note,
                    onValueChange = { if (it.length <= NOTE_MAX) note = it },
                    enabled = !sending,
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text(stringResource(R.string.nm_report_note_hint), fontSize = 14.sp) },
                    supportingText = { Text("${note.length}/$NOTE_MAX", fontSize = 12.sp, color = muted) },
                    minLines = 2,
                    maxLines = 4,
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = reason != null && !sending,
                onClick = {
                    val why = reason ?: return@TextButton
                    sending = true
                    scope.launch {
                        val outcome = NanoMuseCloud.reportAiOutput(context, why.wire, modelId, text, note.trim())
                        sending = false
                        when (outcome) {
                            NanoMuseCloud.ReportOutcome.SENT -> {
                                toast(context, R.string.nm_report_sent)
                                onDone()
                            }
                            NanoMuseCloud.ReportOutcome.RATE_LIMITED -> toast(context, R.string.nm_report_rate_limited)
                            NanoMuseCloud.ReportOutcome.FAILED -> toast(context, R.string.nm_report_failed)
                            NanoMuseCloud.ReportOutcome.NO_ACCOUNT -> {
                                // No FOMO Cloud account: the report goes by e-mail instead.
                                val to = NanoMuseCloud.supportEmail(context)
                                if (sendByMail(context, to, why, note.trim(), text)) {
                                    toast(context, R.string.nm_report_sent)
                                    onDone()
                                } else {
                                    Toast.makeText(context, context.getString(R.string.nm_report_no_mail_app, to), Toast.LENGTH_LONG).show()
                                }
                            }
                        }
                    }
                },
            ) {
                if (sending) {
                    CircularProgressIndicator(Modifier.width(16.dp).height(16.dp), strokeWidth = 2.dp, color = MuseTones.action)
                } else {
                    Text(stringResource(R.string.nm_report_send), color = if (reason != null) MuseTones.action else muted)
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDone, enabled = !sending) { Text(stringResource(R.string.nm_cancel)) }
        },
    )
}

private fun toast(context: Context, resId: Int) {
    Toast.makeText(context, context.getString(resId), Toast.LENGTH_SHORT).show()
}

/** Opens the mail app with the report filled in. False when the phone has no mail app. */
private fun sendByMail(context: Context, to: String, reason: ReportReason, note: String, text: String): Boolean {
    val body = buildString {
        append(context.getString(R.string.nm_report_email_reason, context.getString(reason.label)))
        append('\n')
        if (note.isNotBlank()) {
            append(context.getString(R.string.nm_report_email_note, note))
            append('\n')
        }
        append('\n')
        append(context.getString(R.string.nm_report_email_reply))
        append('\n')
        append(text.take(NanoMuseCloud.REPORT_TEXT_MAX))
    }
    val intent = Intent(Intent.ACTION_SENDTO).apply {
        data = Uri.parse("mailto:")
        putExtra(Intent.EXTRA_EMAIL, arrayOf(to))
        putExtra(Intent.EXTRA_SUBJECT, context.getString(R.string.nm_report_email_subject))
        putExtra(Intent.EXTRA_TEXT, body)
        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
    return try {
        context.startActivity(intent)
        true
    } catch (_: ActivityNotFoundException) {
        false
    } catch (_: Throwable) {
        false
    }
}
