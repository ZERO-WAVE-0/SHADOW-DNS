```


                                                  
 ▗▄▖ ▗▖ ▗▖  ▄  ▗▄▄   ▗▄▖ ▄   ▄     ▗▄▄  ▗▄ ▗▖ ▗▄▖ 
▗▛▀▜ ▐▌ ▐▌ ▐█▌ ▐▛▀█  █▀█ █   █     ▐▛▀█ ▐█ ▐▌▗▛▀▜ 
▐▙   ▐▌ ▐▌ ▐█▌ ▐▌ ▐▌▐▌ ▐▌▜▖█▗▛     ▐▌ ▐▌▐▛▌▐▌▐▙   
 ▜█▙ ▐███▌ █ █ ▐▌ ▐▌▐▌ ▐▌▐▌█▐▌     ▐▌ ▐▌▐▌█▐▌ ▜█▙ 
   ▜▌▐▌ ▐▌ ███ ▐▌ ▐▌▐▌ ▐▌▐█▀█▌ ██▌ ▐▌ ▐▌▐▌▐▟▌   ▜▌
▐▄▄▟▘▐▌ ▐▌▗█ █▖▐▙▄█  █▄█ ▐█ █▌     ▐▙▄█ ▐▌ █▌▐▄▄▟▘
 ▀▀▘ ▝▘ ▝▘▝▘ ▝▘▝▀▀   ▝▀▘ ▝▀ ▀▘     ▝▀▀  ▝▘ ▀▘ ▀▀▘ 
                                                  
                                                  

```
# SHADOW-DNS

**SHADOW-DNS** হলো একটি Termux-ফ্রেন্ডলি পাইথন টুল যা লোকাল ফোল্ডারকে HTTP সার্ভার হিসেবে চালিয়ে ইন্টারনেটে শেয়ারযোগ্য পাবলিক URL তৈরি করে। এটি স্বয়ংক্রিয়ভাবে Cloudflared অথবা localhost.run টানেল ব্যবহার করে এবং কালার-কোডেড লগ দেখায়। ব্যক্তিগত প্রোজেক্ট, ফাইল শেয়ার বা টেস্টিং-এর জন্য এটি সহজ ও হালকা সমাধান।  

---

## ✨ Features
- লোকাল ফোল্ডার সার্ভ করে HTTP এর মাধ্যমে অ্যাক্সেসযোগ্য করে  
- Cloudflared / localhost.run টানেল সাপোর্ট  
- স্বয়ংক্রিয় পোর্ট চেক  
- কালার-কোডেড টার্মিনাল লগ  
- Termux ফ্রেন্ডলি  

---

## 📦 Installation (Termux)
```bash
pkg update && pkg upgrade -y
pkg install python openssh git -y
pkg install cloudflared -y   # optional but recommended
```

---

🚀 Usage

# Run default (current folder on port 8000)
```

python SHADOW-DNS.py

```
# Serve specific folder on custom port
```

python SHADOW-DNS.py -p 9000 -d /sdcard/Download

```
# Only local server (no public tunnel)
```
python SHADOW-DNS.py --no-public
```

---

🛑 Stop the Tool

Ctrl + C চাপলেই সার্ভার এবং টানেল দুটোই বন্ধ হবে।


---

⚠️ Disclaimer

এই টুলটি শুধুমাত্র শিক্ষামূলক ও ব্যক্তিগত কাজে ব্যবহারের জন্য তৈরি। যেকোনো প্রকার অপব্যবহারের দায়ভার সম্পূর্ণ ব্যবহারকারীর উপর বর্তাবে।
