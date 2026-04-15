# Momi Repairing Works - New Features Guide

## Overview
Your website has been updated with modern features and improved UI/UX. Here's what's new:

---

## 1. Add to Cart Feature

### For Customers:
- **Where to See It**: Cart icon and button appear on all pages in the sidebar and hero section
- **How to Use**:
  1. Browse services on the Services page
  2. Click "View Cart" button to open the cart modal
  3. Cart items are stored locally on the customer's device
  4. Click "Continue to Order" to send selected items to WhatsApp
  5. Chat directly with admin via WhatsApp to place order

- **Features**:
  - Cart persists across page refreshes (uses browser's localStorage)
  - Shows total number of items
  - Easy remove functionality
  - Beautiful notification on item add
  - Mobile-friendly cart modal

### Technical Details:
- Uses browser's localStorage (`mrw_cart` key)
- Cart data includes: item name, details, timestamp
- Checkout integrates with WhatsApp API
- No server storage required for cart (operates client-side)

---

## 2. Admin Service Controls

### For Admin:
- **Where to Find It**: Admin Dashboard → Service Visibility Controls section
- **How to Use**:
  1. Log in to admin dashboard
  2. Scroll to "Service Visibility Controls" section
  3. Toggle switches for each service (Agriculture, Doors, Chogaths)
  4. Green = Service visible to customers
  5. Gray = Service hidden from customers
  6. Click "Save Service Settings" button

- **What Gets Hidden**:
  - Service item on homepage "Our Services" preview
  - Entire service page section (Agriculture/Doors/Chogaths)
  - Service in service preview grid

- **Features**:
  - Settings persist across sessions (localStorage)
  - Real-time visual feedback
  - Quick enable/disable without editing content

### Technical Details:
- Uses localStorage (`mrw_service_states` key)
- Settings applied instantly on save (page reloads)
- Checks localStorage first, then checks service data structure
- Applies to frontend visibility only

---

## 3. Quick Contact Section

### For Customers:
- **Location**: Top of homepage (after hero section)
- **Features**:
  - Quick display of business contact info (phone, address, email)
  - Fast enquiry form with less fields than full contact page
  - Direct clickable phone and email links
  - Integrates with main enquiry system

- **How to Use Quick Enquiry**:
  1. Enter name and phone (required)
  2. Type brief message
  3. Click "Send"
  4. Confirmation message appears
  5. Admin receives enquiry in dashboard

---

## 4. Hidden Admin Login

### Security Feature:
- **Removed from**: All public navigation menus
- **Access**: Direct URL at `/admin` (serves dedicated login page)
- **Why**: Keeps admin interface hidden from casual users
- **For Admins**: Bookmark the admin login page or use:
  - `http://yoursite.com/admin`
  - `http://yoursite.com/admin-dashboard.html` (redirects to login if not authenticated)

---

## 5. UI/UX Improvements

### Modern Design Elements:
- ✨ **Soft Shadows**: Enhanced depth throughout
- 📐 **Better Spacing**: Improved padding and margins
- 🎨 **Color Scheme**: Clean white background with professional colors
- 💫 **Smooth Animations**: Hover effects and transitions
- 📱 **Responsive Layout**: Works perfectly on mobile, tablet, desktop

### Specific Improvements:
- Service boxes have better hover states
- Machine repair cards have improved shadows
- Buttons have better visual feedback
- Forms have better focus states
- Modal has smooth animations
- Footer has improved contrast
- Navigation is cleaner

### Responsive Features:
- Mobile-first approach
- Adaptive grid layouts
- Touch-friendly buttons and inputs
- Readable text at all sizes
- Optimized for small screens

---

## 6. Data Structure Changes

### Service Format (Backend):
Previously:
```json
"services": {
  "agriculture": "Description text...",
  "doors": "Description text...",
  "chogaths": "Description text..."
}
```

Now:
```json
"services": {
  "agriculture": {
    "description": "Description text...",
    "enabled": true
  },
  "doors": {
    "description": "Description text...",
    "enabled": true
  },
  "chogaths": {
    "description": "Description text...",
    "enabled": false
  }
}
```

**Backward Compatibility**: Code handles both old and new formats automatically.

---

## 7. Storage & Data

### Client-Side Storage (LocalStorage):
- `mrw_cart`: Cart items (JSON array)
- `mrw_service_states`: Service visible/hidden states (JSON object)

These are cleared only when customer clears browser data.

### Server-Side Storage:
- Enquiries: Sent and stored on server via `/api/public/enquiries`
- Orders: Sent and stored on server via `/api/public/orders`
- Business Info: Stored in `data/site-data.json`
- Photos: Stored in `uploads/` directories

---

## 8. Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Android)

---

## 9. Performance

- **Fast Loading**: Minimal dependencies
- **No External Libraries**: Uses vanilla JavaScript
- **Efficient Storage**: LocalStorage-based caching
- **Optimized Images**: Use WebP format when possible
- **Mobile Optimized**: Responsive CSS with mobile-first approach

---

## 10. Admin Checklist

When setting up the website:

- [ ] Update business information in admin dashboard
- [ ] Add service descriptions and set enabled/disabled status
- [ ] Upload photos for each service category
- [ ] Test cart functionality
- [ ] Test quick contact form
- [ ] Verify service visibility toggles
- [ ] Test checkout process (WhatsApp integration)
- [ ] Configure WhatsApp number in business info

---

## 11. Common Tasks

### Update Service Description:
1. Go to Admin Dashboard
2. Section: "Service Descriptions"
3. Edit text for Agriculture/Doors/Chogaths
4. Click "Save Service Descriptions"

### Hide a Service from Customers:
1. Go to Admin Dashboard
2. Section: "Service Visibility Controls"
3. Click toggle switch for the service (turns gray)
4. Click "Save Service Settings"

### Add Item to Cart (as Customer):
1. Visit Services page
2. Click "View Cart" in sidebar
3. Use checkout to send order via WhatsApp

### Clear Cart (as Customer):
1. Open cart modal
2. Remove all items individually
3. Cart automatically updates

### Respond to Quick Enquiry:
1. Go to Admin Dashboard
2. Section: "Enquiries List"
3. Find enquiry with "Quick Enquiry" service
4. Call or WhatsApp customer at provided number

---

## 12. Troubleshooting

### Cart not showing items:
- Check browser supports localStorage
- Clear browser cache and try again
- Try in incognito/private mode

### Service still visible after toggling:
- Click "Save Service Settings" button
- Wait for page to reload
- Check localStorage isn't full

### Quick contact form not sending:
- Verify JavaScript is enabled
- Check browser console for errors
- Ensure admin enquiries endpoint is working

### WhatsApp checkout not working:
- Verify WhatsApp number is set in business info
- Check number format: country code + number
- Ensure customer has WhatsApp installed or web.whatsapp.com accessible

---

## 13. Future Enhancements (Optional)

Consider adding:
- Shopping cart with pricing
- Service ratings and reviews
- Customer dashboard
- Order tracking
- Photo galleries with lightbox
- Blog or company news
- Live chat support
- Email notifications for enquiries

---

## 14. Support & Maintenance

### Regular Tasks:
- Update photos monthly
- Review and respond to enquiries daily
- Backup data files weekly
- Monitor cart analytics monthly

### Contact Information:
- Website: Your Site URL
- Admin: /admin (serves admin-login.html)
- Orders: Managed via WhatsApp

---

**Website Version**: 2.0 (Updated March 2026)
**Last Updated**: March 21, 2026
**Maintained By**: Admin Team
