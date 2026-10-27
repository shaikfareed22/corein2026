package io.github.nanomuse.ui.muse

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.openminis.app.R

/**
 * The FOMO logo as a hero, on its own navy with rounded corners (drawable-nodpi/nm_fomo_logo.png,
 * from assets/brand/fomo-logo.png). For the screens that are about the app and the account —
 * sign-in, the first-run door — where the face would promise a conversation that is not there
 * yet. [size] is the logo's height; it is about two and a half times as wide.
 */
@Composable
fun NmBrandMark(size: Dp = 104.dp, modifier: Modifier = Modifier) {
    Image(
        painter = painterResource(R.drawable.nm_fomo_logo),
        contentDescription = "FOMO",
        contentScale = ContentScale.Fit,
        modifier = modifier
            .height(size)
            .width(size * 2.45f)
            .clip(RoundedCornerShape(size * 0.18f)),
    )
}
