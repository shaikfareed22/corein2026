package io.github.nanomuse.ui.hands

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog as ComposeAlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.openminis.app.R
import com.openminis.app.accessibility.MinisAccessibilityService
import io.github.nanomuse.ui.home.MuseTones

/**
 * The prominent disclosure Google Play asks for before an app sends the user to turn on an
 * accessibility service: what FOMO Hands reads, when it does nothing, where the screenshots go,
 * and how to turn it off again. Every path that opens Settings → Accessibility goes through
 * here, so the words are shown each time until the service is actually on; a dismissal is
 * never remembered.
 */
object HandsDisclosure {

    /** Whether the FOMO accessibility service is on: enabled in Settings, or bound right now. */
    fun serviceOn(context: Context): Boolean {
        if (MinisAccessibilityService.getInstance() != null) return true
        val expected = "${context.packageName}/${MinisAccessibilityService::class.java.name}"
        val enabled = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
        ) ?: return false
        return enabled.split(':').any { it.equals(expected, ignoreCase = true) }
    }

    /** Opens Settings → Accessibility; plain Settings when an OEM hides that panel. Call only after consent. */
    fun openAccessibilitySettings(context: Context) {
        try {
            context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        } catch (_: Throwable) {
            runCatching { context.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        }
    }

    /** The body as one text, for the classic dialog and for anything that cannot host Compose. */
    fun bodyText(context: Context): String = listOf(
        context.getString(R.string.nm_hands_disclosure_p1),
        context.getString(R.string.nm_hands_disclosure_p2),
        context.getString(R.string.nm_hands_disclosure_p3),
        context.getString(R.string.nm_hands_disclosure_footer),
    ).joinToString("\n\n")

    /**
     * The same disclosure as a classic [AlertDialog], for an Activity that is not inside a
     * composition (MainActivity's repair prompt). [onContinue] runs after the user consents and
     * Settings has been opened; [onNotNow] on the other button, back press or an outside tap.
     * When the service is already on there is nothing to disclose and Settings opens at once.
     */
    fun show(context: Context, onContinue: () -> Unit, onNotNow: () -> Unit = {}) {
        if (serviceOn(context)) {
            openAccessibilitySettings(context)
            onContinue()
            return
        }
        var decided = false
        AlertDialog.Builder(context)
            .setTitle(R.string.nm_hands_disclosure_title)
            .setMessage(bodyText(context))
            .setCancelable(true)
            .setOnCancelListener { if (!decided) { decided = true; onNotNow() } }
            .setNegativeButton(R.string.nm_hands_disclosure_not_now) { d, _ ->
                d.dismiss()
                if (!decided) { decided = true; onNotNow() }
            }
            .setPositiveButton(R.string.nm_hands_disclosure_continue) { d, _ ->
                d.dismiss()
                if (!decided) {
                    decided = true
                    openAccessibilitySettings(context)
                    onContinue()
                }
            }
            .show()
    }
}

/**
 * The disclosure as a Compose dialog. [onContinue] is the consent button: the caller opens
 * Settings there (see [rememberHandsAccessibilityOpener], which does both).
 */
@Composable
fun HandsDisclosureDialog(onContinue: () -> Unit, onDismiss: () -> Unit) {
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    ComposeAlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.nm_hands_disclosure_title)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                DisclosurePoint(stringResource(R.string.nm_hands_disclosure_p1))
                Spacer(Modifier.height(8.dp))
                DisclosurePoint(stringResource(R.string.nm_hands_disclosure_p2))
                Spacer(Modifier.height(8.dp))
                DisclosurePoint(stringResource(R.string.nm_hands_disclosure_p3))
                Spacer(Modifier.height(12.dp))
                Text(stringResource(R.string.nm_hands_disclosure_footer), fontSize = 12.sp, lineHeight = 16.sp, color = muted)
            }
        },
        confirmButton = {
            TextButton(onClick = onContinue) {
                Text(stringResource(R.string.nm_hands_disclosure_continue), color = MuseTones.action)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text(stringResource(R.string.nm_hands_disclosure_not_now)) }
        },
    )
}

@Composable
private fun DisclosurePoint(text: String) {
    Row(Modifier.padding(end = 4.dp)) {
        Text("•", fontSize = 14.sp, lineHeight = 20.sp)
        Spacer(Modifier.width(8.dp))
        Text(text, fontSize = 14.sp, lineHeight = 20.sp)
    }
}

/**
 * The one way a screen sends the user to Settings → Accessibility. Returns the action to put
 * on the button: it shows [HandsDisclosureDialog] first and opens Settings only from the
 * consent button. With the service already on (the user is going there to turn it off) the
 * dialog is skipped. The dialog is hosted here, so a caller only invokes the returned lambda.
 */
@Composable
fun rememberHandsAccessibilityOpener(): () -> Unit {
    val context = LocalContext.current
    var show by remember { mutableStateOf(false) }
    if (show) {
        HandsDisclosureDialog(
            onContinue = {
                show = false
                HandsDisclosure.openAccessibilitySettings(context)
            },
            onDismiss = { show = false },
        )
    }
    val opener: () -> Unit = remember(context) {
        {
            if (HandsDisclosure.serviceOn(context)) {
                HandsDisclosure.openAccessibilitySettings(context)
            } else {
                show = true
            }
        }
    }
    return opener
}
