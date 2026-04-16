import { ClerkProvider, SignInButton, UserButton } from '@clerk/nextjs'
import { auth } from '@clerk/nextjs/server' // 🔴 ابزار قدرتمند چک کردن لاگین در سرور
import './globals.css'

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // 🔴 سرور اینجا چک می‌کند که آیا کاربری وجود دارد یا خیر
  const { userId } = await auth();

  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          {/* هدر سایت */}
          <header className="flex justify-end items-center p-4 bg-white border-b border-gray-100 shadow-sm">
            {userId ? (
              // اگر کاربر لاگین بود، عکس پروفایلش را نشان بده
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500 mr-4">Secure Session Active</span>
                <UserButton afterSignOutUrl="/" />
              </div>
            ) : (
              // اگر لاگین نبود، دکمه لاگین را نشان بده
              <div className="bg-[#209DD7] text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-[#1a85b6] transition-colors shadow-sm">
                <SignInButton mode="modal" />
              </div>
            )}
          </header>
          
          {/* محتوای اصلی صفحه (چت‌باکس ما) */}
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}