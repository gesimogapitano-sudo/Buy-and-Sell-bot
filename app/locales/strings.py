"""
Bilingual string constants for the Buy & Sell Marketplace Bot.

Supports English (en) and Amharic (am).
Usage:
    from app.locales.strings import t
    text = t("welcome", lang="en")
"""

from __future__ import annotations

from typing import Any, Dict

# ---------------------------------------------------------------------------
# String catalogue
# ---------------------------------------------------------------------------

_STRINGS: Dict[str, Dict[str, str]] = {
    # ── General ──────────────────────────────────────────────────────────
    "btn_cancel": {"en": "❌ Cancel", "am": "❌ ሰርዝ"},
    "btn_back": {"en": "◀️ Back", "am": "◀️ ተመለስ"},
    "btn_yes": {"en": "✅ Yes", "am": "✅ አዎ"},
    "btn_no": {"en": "❌ No", "am": "❌ አይ"},
    "btn_skip": {"en": "⏭️ Skip", "am": "⏭️ ዝለል"},
    "btn_done": {"en": "✅ Done", "am": "✅ ተጠናቋል"},
    "action_cancelled": {"en": "❌ Action cancelled.", "am": "❌ ተግባሩ ተሰርዟል።"},
    "error_generic": {
        "en": "⚠️ Something went wrong. Please try again.",
        "am": "⚠️ ችግር ተፈጥሯል። እባክዎ እንደገና ሞክሩ።",
    },
    "not_authorized": {
        "en": "🚫 You are not authorized to perform this action.",
        "am": "🚫 ይህን ድርጊት ለማከናወን ፈቃድ የለዎትም።",
    },

    # ── Consent / Privacy ─────────────────────────────────────────────────
    "consent_required": {
        "en": (
            "👋 <b>Welcome to the Marketplace!</b>\n\n"
            "Before you continue, please read and accept our "
            "<b>Privacy Notice</b>.\n\n"
            "We collect only the data necessary to operate this service. "
            "You can withdraw consent at any time via /settings."
        ),
        "am": (
            "👋 <b>ወደ ገበያ ቦታ እንኳን ደህና መጡ!</b>\n\n"
            "ከመቀጠልዎ በፊት እባክዎ የ<b>ግላዊነት ማስታወቂያ</b>ን ያንብቡ እና ይቀበሉ።\n\n"
            "አገልግሎቱን ለማስኬድ አስፈላጊ ውሂብ ብቻ እንሰበስባለን። "
            "ፈቃዱን በማንኛውም ጊዜ /settings ን በመጠቀም መሰርዝ ይችላሉ።"
        ),
    },
    "btn_accept_consent": {"en": "✅ Accept & Continue", "am": "✅ ተቀበል እና ቀጥል"},
    "btn_decline_consent": {"en": "❌ Decline", "am": "❌ አልቀበልም"},
    "consent_declined": {
        "en": "You have declined. You cannot use the bot without accepting the privacy notice.",
        "am": "ፈቃዱን አልተቀበሉም። የግላዊነት ማስታወቂያ ሳይቀበሉ ቦቱን መጠቀም አይቻልም።",
    },
    "consent_accepted": {
        "en": "✅ Thank you! You can now use all features.",
        "am": "✅ አመሰግናለሁ! አሁን ሁሉንም ባህሪያት መጠቀም ይችላሉ።",
    },

    # ── /start ────────────────────────────────────────────────────────────
    "welcome": {
        "en": (
            "🛒 <b>Buy & Sell Marketplace</b>\n\n"
            "Buy and sell anything easily through Telegram.\n\n"
            "Use the menu below to get started:"
        ),
        "am": (
            "🛒 <b>የግዢ እና ሽያጭ ገበያ</b>\n\n"
            "በቴሌግራም በኩል ማንኛውንም ነገር በቀላሉ ይሸጡ እና ይግዙ።\n\n"
            "ለመጀመር ከታች ያለውን ሜኑ ይጠቀሙ:"
        ),
    },
    "btn_sell": {"en": "🏷️ Sell Something", "am": "🏷️ ሽያጭ ጀምር"},
    "btn_my_listings": {"en": "📋 My Listings", "am": "📋 ማስታወቂያዎቼ"},
    "btn_messages": {"en": "💬 Messages", "am": "💬 መልዕክቶች"},
    "btn_settings": {"en": "⚙️ Settings", "am": "⚙️ ቅንብሮች"},
    "btn_help": {"en": "❓ Help", "am": "❓ እርዳታ"},
    "btn_admin_panel": {"en": "🔑 Admin Panel", "am": "🔑 የአስተዳዳሪ ፓነል"},

    "help_text": {
        "en": (
            "📖 <b>How to use this bot:</b>\n\n"
            "🏷️ <b>Sell</b> — Create a new listing with photos, description and price.\n"
            "📋 <b>My Listings</b> — View, edit or withdraw your active listings.\n"
            "💬 <b>Messages</b> — Chat with buyers/sellers anonymously.\n"
            "⚙️ <b>Settings</b> — Change language or manage your data.\n\n"
            "All listings are reviewed by our moderation team before publishing."
        ),
        "am": (
            "📖 <b>ቦቱን እንዴት እንደሚጠቀሙ:</b>\n\n"
            "🏷️ <b>ሽያጭ</b> — ፎቶ፣ መግለጫ እና ዋጋ ያለው አዲስ ማስታወቂያ ይፍጠሩ።\n"
            "📋 <b>ማስታወቂያዎቼ</b> — ንቁ ማስታወቂያዎችዎን ይዩ፣ ያርትዑ ወይም ያስወጡ።\n"
            "💬 <b>መልዕክቶች</b> — ከገዢዎች/ሻጮች ጋር ስም ሳይታወቅ ይጫወቱ።\n"
            "⚙️ <b>ቅንብሮች</b> — ቋንቋ ይቀይሩ ወይም መረጃዎን ያስተዳድሩ።\n\n"
            "ሁሉም ማስታወቂያዎች ከመታተሙ በፊት በቡድናችን ይገመገማሉ።"
        ),
    },

    # ── Listing creation ──────────────────────────────────────────────────
    "listing_type_prompt": {
        "en": "What are you selling?",
        "am": "ምን እየሸጡ ነዎት?",
    },
    "btn_type_product": {"en": "📦 Product", "am": "📦 ምርት"},
    "btn_type_service": {"en": "🛠️ Service", "am": "🛠️ አገልግሎት"},

    "category_prompt": {
        "en": "Select a category for your listing:",
        "am": "ለማስታወቂያዎ ምድብ ይምረጡ:",
    },

    "title_prompt": {
        "en": "📝 Enter a title for your listing:\n<i>(3-100 characters)</i>",
        "am": "📝 ለማስታወቂያዎ ርዕስ ያስገቡ:\n<i>(3-100 ቁምፊዎች)</i>",
    },

    "description_prompt": {
        "en": "📄 Write a description:\n<i>(10-2000 characters)</i>",
        "am": "📄 መግለጫ ይፃፉ:\n<i>(10-2000 ቁምፊዎች)</i>",
    },

    "brand_prompt": {
        "en": "🏷️ Enter brand/make (optional, tap Skip to skip):",
        "am": "🏷️ ብራንድ/አምራቺ ያስገቡ (አማራጭ):",
    },

    "condition_prompt": {
        "en": "🔍 What is the condition of the item?",
        "am": "🔍 የዕቃው ሁኔታ ምን ይመስላል?",
    },
    "btn_condition_new": {"en": "✨ New", "am": "✨ አዲስ"},
    "btn_condition_like_new": {"en": "🌟 Like New", "am": "🌟 እንደ አዲስ"},
    "btn_condition_used": {"en": "👍 Used", "am": "👍 ያገለገለ"},
    "btn_condition_refurbished": {"en": "🔧 Refurbished", "am": "🔧 ታድሷ"},

    "price_prompt": {
        "en": "💰 Enter the price (numbers only, e.g. 15000):",
        "am": "💰 ዋጋ ያስገቡ (ቁጥሮች ብቻ፣ ለምሳሌ 15000):",
    },

    "currency_prompt": {
        "en": "💱 Select currency:",
        "am": "💱 ምንዛሬ ይምረጡ:",
    },

    "location_prompt": {
        "en": "📍 Enter the item location (city/area):",
        "am": "📍 የዕቃው አካባቢ ያስገቡ (ከተማ/ቦታ):",
    },

    "photos_prompt": {
        "en": (
            "📸 Send photos of your item (up to {max} photos).\n\n"
            "Send them one by one, then tap Done."
        ),
        "am": (
            "📸 የዕቃዎ ፎቶዎች ያላኩ (እስከ {max} ፎቶዎች)።\n\n"
            "አንድ በአንድ ያላኩ፣ ከዚያ ተጠናቋልን ይጫኑ።"
        ),
    },
    "photo_added": {
        "en": "✅ Photo added ({current}/{max}). Send another or tap Done.",
        "am": "✅ ፎቶ ታክሏል ({current}/{max}). ሌላ ያላኩ ወይም ተጠናቋልን ይጫኑ።",
    },
    "photos_max_reached": {
        "en": "📸 Maximum photos reached ({max}). Tap Done to continue.",
        "am": "📸 ከፍተኛው ፎቶ ተደርሷል ({max}). ለመቀጠል ተጠናቋልን ይጫኑ።",
    },
    "photos_required": {
        "en": "⚠️ Please send at least one photo before continuing.",
        "am": "⚠️ ከመቀጠልዎ በፊት እባክዎ ቢያንስ አንድ ፎቶ ያላኩ።",
    },

    "listing_preview": {
        "en": (
            "📋 <b>Listing Preview</b>\n\n"
            "<b>Type:</b> {listing_type}\n"
            "<b>Category:</b> {category}\n"
            "<b>Title:</b> {title}\n"
            "<b>Description:</b> {description}\n"
            "<b>Brand:</b> {brand}\n"
            "<b>Condition:</b> {condition}\n"
            "<b>Price:</b> {price}\n"
            "<b>Location:</b> {location}\n\n"
            "Does everything look correct?"
        ),
        "am": (
            "📋 <b>የማስታወቂያ ቅድመ ዕይታ</b>\n\n"
            "<b>ዓይነት:</b> {listing_type}\n"
            "<b>ምድብ:</b> {category}\n"
            "<b>ርዕስ:</b> {title}\n"
            "<b>መግለጫ:</b> {description}\n"
            "<b>ብራንድ:</b> {brand}\n"
            "<b>ሁኔታ:</b> {condition}\n"
            "<b>ዋጋ:</b> {price}\n"
            "<b>አካባቢ:</b> {location}\n\n"
            "ሁሉም ነገር ትክክል ነው?"
        ),
    },
    "btn_submit_listing": {"en": "🚀 Submit for Review", "am": "🚀 ለክለሳ አስገባ"},
    "listing_submitted": {
        "en": (
            "✅ <b>Listing submitted!</b>\n\n"
            "Your listing is now pending review. "
            "You'll be notified once it's approved or if changes are needed."
        ),
        "am": (
            "✅ <b>ማስታወቂያ ቀርቧል!</b>\n\n"
            "ማስታወቂያዎ አሁን በክለሳ ላይ ነው። "
            "ከፀደቀ ወይም ለውጦች ከሚያስፈልጉ ታወቃላቸዋለህ።"
        ),
    },
    "listing_limit_reached": {
        "en": "⚠️ You have reached the maximum number of active listings ({limit}).",
        "am": "⚠️ ከፍተኛ የንቁ ማስታወቂያ ቁጥር ({limit}) ደርሰዋል።",
    },

    # ── My Listings ───────────────────────────────────────────────────────
    "my_listings_empty": {
        "en": "You have no listings yet. Tap Sell Something to create one!",
        "am": "እስካሁን ምንም ማስታወቂያ የለዎትም። ለመፍጠር ሽያጭ ጀምርን ይጫኑ!",
    },
    "my_listings_header": {
        "en": "📋 <b>My Listings</b> (Page {page}/{total_pages}):",
        "am": "📋 <b>ማስታወቂያዎቼ</b> (ገጽ {page}/{total_pages}):",
    },
    "listing_detail": {
        "en": (
            "📌 <b>{title}</b>\n"
            "Status: {status}\n"
            "Price: {price}\n"
            "Category: {category}\n"
            "Posted: {created_at}"
        ),
        "am": (
            "📌 <b>{title}</b>\n"
            "ሁኔታ: {status}\n"
            "ዋጋ: {price}\n"
            "ምድብ: {category}\n"
            "ቀን: {created_at}"
        ),
    },
    "btn_withdraw_listing": {"en": "↩️ Withdraw", "am": "↩️ አስወጣ"},
    "btn_mark_sold": {"en": "🏷️ Mark as Sold", "am": "🏷️ እንደ ተሸጠ ምልክት አድርግ"},
    "btn_view_channel": {"en": "📢 View in Channel", "am": "📢 በቻናሉ ላይ ይዩ"},
    "listing_withdrawn": {
        "en": "✅ Listing withdrawn successfully.",
        "am": "✅ ማስታወቂያ ተስወጥቷል።",
    },
    "listing_marked_sold": {
        "en": "🏷️ Listing marked as sold.",
        "am": "🏷️ ማስታወቂያ እንደ ተሸጠ ምልክት ተደርጓል።",
    },
    "listing_not_found": {
        "en": "⚠️ Listing not found.",
        "am": "⚠️ ማስታወቂያ አልተገኘም።",
    },

    # ── Messaging ─────────────────────────────────────────────────────────
    "contact_seller_btn": {"en": "💬 Contact Seller", "am": "💬 ሻጩን ያግኙ"},
    "conversation_started": {
        "en": (
            "💬 <b>Conversation started!</b>\n\n"
            "You are now chatting with the seller about:\n"
            "<b>{listing_title}</b>\n\n"
            "Your messages are relayed anonymously. "
            "Type your message below."
        ),
        "am": (
            "💬 <b>ውይይት ተጀምሯል!</b>\n\n"
            "አሁን ስለሚከተለው ከሻጩ ጋር እየተነጋገሩ ነዎት:\n"
            "<b>{listing_title}</b>\n\n"
            "መልዕክቶቻቸዎ ስም ሳይታወቅ ይተላለፋሉ። "
            "ከታች መልዕክትዎን ይፃፉ።"
        ),
    },
    "seller_new_inquiry": {
        "en": (
            "📨 <b>New message about your listing!</b>\n\n"
            "<b>{listing_title}</b>\n\n"
            "Buyer says:\n{message}\n\n"
            "Reply to this message to respond."
        ),
        "am": (
            "📨 <b>ስለ ማስታወቂያዎ አዲስ መልዕክት!</b>\n\n"
            "<b>{listing_title}</b>\n\n"
            "ገዢው ይላል:\n{message}\n\n"
            "ለመመለስ ለዚህ መልዕክት ይመልሱ።"
        ),
    },
    "message_relayed": {
        "en": "✅ Message sent.",
        "am": "✅ መልዕክት ተላከ።",
    },
    "message_relay_failed": {
        "en": "⚠️ Could not deliver message. The other party may have blocked the bot.",
        "am": "⚠️ መልዕክት ማድረስ አልተቻለም። ሌላኛው ሰው ቦቱን ሊዘጋ ይችላል።",
    },
    "cannot_message_own_listing": {
        "en": "🚫 You cannot contact yourself about your own listing.",
        "am": "🚫 ስለ ራስዎ ማስታወቂያ ራስዎን ማናገር አይቻልም።",
    },
    "conversation_ended": {
        "en": "❌ This conversation has ended.",
        "am": "❌ ይህ ውይይት አብቅቷል።",
    },
    "my_messages_empty": {
        "en": "You have no active conversations.",
        "am": "ምንም ንቁ ውይይቶች የሉዎትም።",
    },
    "conversation_header": {
        "en": "💬 <b>Conversation</b> about <b>{listing_title}</b>\n{other_party}",
        "am": "💬 <b>ውይይት</b> ስለ <b>{listing_title}</b>\n{other_party}",
    },
    "btn_end_conversation": {"en": "❌ End Conversation", "am": "❌ ውይይቱን አቁም"},

    # ── Reports ───────────────────────────────────────────────────────────
    "btn_report": {"en": "🚩 Report", "am": "🚩 ሪፖርት አድርግ"},
    "report_reason_prompt": {
        "en": "What is the reason for this report?",
        "am": "የዚህ ሪፖርት ምክንያት ምንድን ነው?",
    },
    "btn_report_spam": {"en": "🗑️ Spam", "am": "🗑️ ስፓም"},
    "btn_report_fraud": {"en": "⚠️ Fraud/Scam", "am": "⚠️ ማጭበርበር"},
    "btn_report_inappropriate": {"en": "🔞 Inappropriate", "am": "🔞 ተገቢ ያልሆነ"},
    "btn_report_prohibited": {"en": "🚫 Prohibited Item", "am": "🚫 የተከለከለ ዕቃ"},
    "btn_report_other": {"en": "📝 Other", "am": "📝 ሌላ"},
    "report_details_prompt": {
        "en": "Please provide more details about your report:",
        "am": "እባክዎ ስለ ሪፖርቱ ተጨማሪ ዝርዝር ያቅርቡ:",
    },
    "report_submitted": {
        "en": "✅ Your report has been submitted. Our team will review it shortly.",
        "am": "✅ ሪፖርትዎ ቀርቧል። ቡድናችን በቅርቡ ይገምግመዋል።",
    },

    # ── Settings ──────────────────────────────────────────────────────────
    "settings_menu": {
        "en": "⚙️ <b>Settings</b>\n\nChoose what you'd like to change:",
        "am": "⚙️ <b>ቅንብሮች</b>\n\nምን መቀየር እንደሚፈልጉ ይምረጡ:",
    },
    "btn_change_language": {"en": "🌐 Change Language", "am": "🌐 ቋንቋ ቀይር"},
    "btn_delete_my_data": {"en": "🗑️ Delete My Data", "am": "🗑️ ውሂቤን ሰርዝ"},
    "language_changed": {
        "en": "✅ Language changed to English.",
        "am": "✅ ቋንቋ ወደ አማርኛ ተቀይሯል።",
    },
    "delete_data_confirm": {
        "en": (
            "⚠️ <b>Are you sure?</b>\n\n"
            "This will delete your account and all your listings. "
            "This action is irreversible."
        ),
        "am": (
            "⚠️ <b>እርግጠኛ ነዎት?</b>\n\n"
            "ይህ መለያዎን እና ሁሉንም ማስታወቂያዎቻቸዎን ይሰርዛል። "
            "ይህ ድርጊት ወደ ኋላ ሊቀለበስ አይችልም።"
        ),
    },
    "data_deleted": {
        "en": "✅ Your data has been deleted. Goodbye!",
        "am": "✅ ውሂቦዎ ተሰርዟል። ደህና ሁኑ!",
    },

    # ── Admin panel ───────────────────────────────────────────────────────
    "admin_panel": {
        "en": (
            "🔑 <b>Admin Panel</b>\n\n"
            "📊 Users: {users}\n"
            "📋 Total Listings: {listings}\n"
            "⏳ Pending Review: {pending}\n"
            "💬 Conversations: {conversations}"
        ),
        "am": (
            "🔑 <b>የአስተዳዳሪ ፓነል</b>\n\n"
            "📊 ተጠቃሚዎች: {users}\n"
            "📋 ጠቅላላ ማስታወቂያዎች: {listings}\n"
            "⏳ በክለሳ ላይ: {pending}\n"
            "💬 ውይይቶች: {conversations}"
        ),
    },
    "btn_review_listings": {"en": "⏳ Review Listings", "am": "⏳ ማስታወቂያዎችን ይገምግሙ"},
    "btn_manage_users": {"en": "👥 Manage Users", "am": "👥 ተጠቃሚዎችን ያስተዳድሩ"},
    "btn_manage_admins": {"en": "👮 Manage Admins", "am": "👮 አስተዳዳሪዎችን ያስተዳድሩ"},
    "btn_view_reports": {"en": "🚩 View Reports", "am": "🚩 ሪፖርቶችን ይዩ"},

    "no_pending_listings": {
        "en": "✅ No listings pending review.",
        "am": "✅ ምንም ማስታወቂያ ለክለሳ አልቀረበም።",
    },
    "review_listing": {
        "en": (
            "📋 <b>Review Listing #{listing_id}</b>\n\n"
            "<b>Seller:</b> {seller}\n"
            "<b>Type:</b> {listing_type}\n"
            "<b>Category:</b> {category}\n"
            "<b>Title:</b> {title}\n"
            "<b>Description:</b>\n{description}\n\n"
            "<b>Brand:</b> {brand}\n"
            "<b>Condition:</b> {condition}\n"
            "<b>Price:</b> {price}\n"
            "<b>Location:</b> {location}\n"
            "<b>Photos:</b> {photos}\n"
            "<b>Submitted:</b> {submitted_at}\n\n"
            "Pending ({current}/{total})"
        ),
        "am": (
            "📋 <b>ማስታወቂያ #{listing_id} ይገምግሙ</b>\n\n"
            "<b>ሻጭ:</b> {seller}\n"
            "<b>ዓይነት:</b> {listing_type}\n"
            "<b>ምድብ:</b> {category}\n"
            "<b>ርዕስ:</b> {title}\n"
            "<b>መግለጫ:</b>\n{description}\n\n"
            "<b>ብራንድ:</b> {brand}\n"
            "<b>ሁኔታ:</b> {condition}\n"
            "<b>ዋጋ:</b> {price}\n"
            "<b>አካባቢ:</b> {location}\n"
            "<b>ፎቶዎች:</b> {photos}\n"
            "<b>የቀረበ:</b> {submitted_at}\n\n"
            "በጥበቃ ({current}/{total})"
        ),
    },
    "btn_approve": {"en": "✅ Approve", "am": "✅ ፍቀድ"},
    "btn_reject": {"en": "❌ Reject", "am": "❌ ውድቅ አድርግ"},
    "btn_request_changes": {"en": "🔄 Request Changes", "am": "🔄 ለውጦች ጠይቅ"},
    "btn_next_listing": {"en": "▶️ Next", "am": "▶️ ቀጣይ"},

    "reject_reason_prompt": {
        "en": "Please enter the reason for rejection:",
        "am": "እባክዎ የውድቅ ምክንያት ያስገቡ:",
    },
    "changes_reason_prompt": {
        "en": "Please describe the changes needed:",
        "am": "እባክዎ የሚያስፈልጉ ለውጦችን ይግለጹ:",
    },

    "listing_approved_seller": {
        "en": (
            "✅ <b>Your listing was approved!</b>\n\n"
            "<b>{title}</b>\n\n"
            "It has been published to the channel."
        ),
        "am": (
            "✅ <b>ማስታወቂያዎ ፀድቋል!</b>\n\n"
            "<b>{title}</b>\n\n"
            "ወደ ቻናሉ ታትሟል።"
        ),
    },
    "listing_rejected_seller": {
        "en": (
            "❌ <b>Your listing was rejected.</b>\n\n"
            "<b>{title}</b>\n\n"
            "<b>Reason:</b> {reason}"
        ),
        "am": (
            "❌ <b>ማስታወቂያዎ ውድቅ ሆኗል።</b>\n\n"
            "<b>{title}</b>\n\n"
            "<b>ምክንያት:</b> {reason}"
        ),
    },
    "listing_changes_requested_seller": {
        "en": (
            "🔄 <b>Changes requested for your listing.</b>\n\n"
            "<b>{title}</b>\n\n"
            "<b>Requested changes:</b> {reason}\n\n"
            "Please withdraw and resubmit your listing with the changes."
        ),
        "am": (
            "🔄 <b>ስለ ማስታወቂያዎ ለውጦች ተጠይቀዋል።</b>\n\n"
            "<b>{title}</b>\n\n"
            "<b>የተጠሩ ለውጦች:</b> {reason}\n\n"
            "ማስታወቂያዎን አስወጥተው ከለውጦቹ ጋር እንደገና ያስገቡ።"
        ),
    },
    "listing_approved_admin": {
        "en": "✅ Listing #{listing_id} approved and published.",
        "am": "✅ ማስታወቂያ #{listing_id} ፀድቆ ታትሟል።",
    },
    "listing_rejected_admin": {
        "en": "❌ Listing #{listing_id} rejected.",
        "am": "❌ ማስታወቂያ #{listing_id} ውድቅ ሆኗል።",
    },

    # ── Channel post ──────────────────────────────────────────────────────
    "channel_post": {
        "en": (
            "🏷️ <b>{title}</b>\n\n"
            "{description}\n\n"
            "💰 <b>Price:</b> {price}\n"
            "📍 <b>Location:</b> {location}\n"
            "🔖 <b>Category:</b> {category}\n"
            "📦 <b>Condition:</b> {condition}\n\n"
            "👉 <a href=\"{contact_link}\">Contact Seller</a>"
        ),
        "am": (
            "🏷️ <b>{title}</b>\n\n"
            "{description}\n\n"
            "💰 <b>ዋጋ:</b> {price}\n"
            "📍 <b>አካባቢ:</b> {location}\n"
            "🔖 <b>ምድብ:</b> {category}\n"
            "📦 <b>ሁኔታ:</b> {condition}\n\n"
            "👉 <a href=\"{contact_link}\">ሻጩን ያናግሩ</a>"
        ),
    },

    # ── Pagination ────────────────────────────────────────────────────────
    "btn_prev": {"en": "◀️ Previous", "am": "◀️ ቀዳሚ"},
    "btn_next": {"en": "▶️ Next", "am": "▶️ ቀጣይ"},
}


def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Translate a string key to the given language.

    Args:
        key: The string key from the catalogue.
        lang: Language code ('en' or 'am').
        **kwargs: Format variables to substitute into the string.

    Returns:
        Translated and formatted string, falling back to English.
    """
    entry = _STRINGS.get(key)
    if not entry:
        return f"[MISSING:{key}]"

    # Fall back to English if language not found
    text = entry.get(lang) or entry.get("en") or f"[MISSING:{key}:{lang}]"

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass  # Return unformatted if substitution fails

    return text
