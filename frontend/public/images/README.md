# Adding Your Hero Image

## Quick Start

1. **Add your image file here:**
   - Place your image in this directory (`/public/images/`)
   - Supported formats: PNG, JPG, JPEG, WebP
   - Recommended name: `hero.png` or `hero.jpg`

2. **Recommended image specs:**
   - **Dimensions**: 1200x675px (16:9 aspect ratio)
   - **File size**: < 500KB (optimize for web)
   - **Format**: PNG or JPG
   - **Content**: Dashboard screenshot, F1 car, or analytics visualization

3. **Update the code:**
   Open `/app/page.tsx` and find line 91-99.

   **Uncomment these lines:**
   ```tsx
   <Image
     src="/images/hero.png"  // Change to your filename
     alt="RacingLineAI Dashboard Preview"
     fill
     className="object-cover"
     priority
   />
   ```

   **Remove the placeholder div** (lines 67-89)

4. **Test it:**
   ```bash
   npm run dev
   ```
   Visit http://localhost:3000 and you should see your image!

## Image Optimization Tips

- Use https://tinypng.com/ to compress images
- Or use Next.js Image Optimization automatically
- WebP format for best quality/size ratio

## Alternative: Use a screenshot

If you want to use a screenshot of your Streamlit dashboard:

1. Take a screenshot of your current dashboard
2. Crop it to 16:9 aspect ratio
3. Save as `hero.png`
4. Place it here and follow steps above

Done! 🎉
