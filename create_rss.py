import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import time
import os
import re

def scrape_newsletter():
    """大江橋法律事務所のニュースレター一覧をスクレイピング"""
    
    # 検索URL（中国最新法律Newsに絞り込み）
    url = "https://www.ohebashi.com/jp/newsletter/search.php"
    
    # 検索パラメータ
    params = {
        'q_title': '中国最新法律News',
        'q_lawyer': '',
        'date_from': '',
        'date_to': ''
    }
    
    # リクエストヘッダー（ブラウザからのアクセスに見せる）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("[ステッカー] ウェブページにアクセス中...")
    
    try:
        # ページを取得
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        print("[ステッカー] ページ取得成功！")
        
    except Exception as e:
        print(f"[ステッカー] ページ取得エラー: {e}")
        return []
    
    # BeautifulSoupで解析
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # ニュースレター一覧を格納するリスト
    articles = []
    
    # HTML構造に基づいて記事を抽出
    # 各記事は <dl> タグで囲まれている
    dl_items = soup.find_all('dl')
    
    for dl in dl_items:
        # dtタグから日付とVolを取得
        dt = dl.find('dt')
        if not dt:
            continue
        
        dt_text = dt.get_text(strip=True)
        
        # 日付を抽出（例：2026.07.24 → 2026-07-24）
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', dt_text)
        if not date_match:
            continue
        
        date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        
        # Vol番号を抽出
        vol_match = re.search(r'Vol\.(\d+)', dt_text)
        vol_str = vol_match.group(1) if vol_match else ""
        
        # ddタグからリンクとタイトルを取得
        dd = dl.find('dd')
        if not dd:
            continue
        
        # PDFリンク（All.pdf）を探す
        pdf_link = None
        pdf_title = None
        
        # dd内のすべてのaタグをチェック
        for a_tag in dd.find_all('a', href=True):
            href = a_tag.get('href')
            title = a_tag.get_text(strip=True)
            
            # PDFファイルへのリンクかつ「All.pdf」を含むものを優先
            if href.endswith('.pdf') and 'All.pdf' in href:
                pdf_link = href
                pdf_title = title
                break
        
        # All.pdfが見つからない場合、最初のPDFリンクを使用
        if not pdf_link:
            for a_tag in dd.find_all('a', href=True):
                href = a_tag.get('href')
                if href.endswith('.pdf'):
                    pdf_link = href
                    pdf_title = a_tag.get_text(strip=True)
                    break
        
        if not pdf_link:
            continue
        
        # 絶対URLに変換
        if pdf_link.startswith('/'):
            pdf_link = 'https://www.ohebashi.com' + pdf_link
        elif not pdf_link.startswith('http'):
            pdf_link = 'https://www.ohebashi.com/jp/newsletter/' + pdf_link
        
        # タイトルが取得できていない場合、Vol番号から作成
        if not pdf_title:
            pdf_title = f"中国最新法律Newsletter Vol.{vol_str}" if vol_str else "中国最新法律Newsletter"
        
        articles.append({
            'title': pdf_title,
            'link': pdf_link,
            'date': date_str,
            'vol': vol_str,
            'description': f"大江橋法律事務所 中国最新法律Newsletter Vol.{vol_str} ({date_str})"
        })
    
    print(f"[ステッカー] {len(articles)}件の記事が見つかりました")
    
    # 日付でソート（新しい順）
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    return articles

def generate_rss(articles):
    """RSSフィードを生成"""
    
    if not articles:
        print("[ステッカー] 記事が見つからないため、RSSを生成しません")
        return
    
    fg = FeedGenerator()
    fg.title('大江橋法律事務所 中国最新法律News RSS')
    fg.description('大江橋法律事務所の中国最新法律Newsに関するニュースレターのRSSフィード')
    fg.link(href='https://www.ohebashi.com/jp/newsletter/search.php?q_title=%E4%B8%AD%E5%9B%BD%E6%9C%80%E6%96%B0%E6%B3%95%E5%BE%8BNews', rel='alternate')
    fg.language('ja')
    
    # 最終更新日時
    fg.lastBuildDate(datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900'))
    
    # 各記事をRSSに追加
    for article in articles[:20]:  # 最新20件まで
        fe = fg.add_entry()
        fe.title(article['title'])
        fe.link(href=article['link'])
        fe.description(article['description'])
        
        # 日付を設定（HTMLから取得した日付を使用）
        if article['date']:
            try:
                # 日付文字列をパース（例：2026-07-24）
                pub_date = datetime.strptime(article['date'], '%Y-%m-%d')
                # RSS仕様に合わせたフォーマットに変換
                fe.pubDate(pub_date.strftime('%a, %d %b %Y %H:%M:%S +0900'))
                print(f"  [ステッカー] {article['title']} -> {pub_date.strftime('%Y-%m-%d')}")
            except Exception as e:
                # パースできない場合は現在時刻
                print(f"  [ステッカー] 日付パースエラー: {article['date']} - {e}")
                fe.pubDate(datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900'))
        else:
            fe.pubDate(datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900'))
        
        # GUID（一意識別子）
        fe.guid(article['link'], permalink=True)
    
    # RSSファイルを保存
    rss_path = 'rss.xml'
    fg.rss_file(rss_path)
    print(f"[ステッカー] RSSフィードを生成しました: {rss_path}")
    
    # ファイルサイズを表示
    file_size = os.path.getsize(rss_path)
    print(f"[ステッカー] ファイルサイズ: {file_size} bytes")

def main():
    """メイン関数"""
    print("[ステッカー] RSSフィード生成を開始します...")
    print("=" * 50)
    
    # スクレイピング実行
    articles = scrape_newsletter()
    
    # RSS生成
    if articles:
        generate_rss(articles)
    else:
        print("[ステッカー] 記事が見つかりませんでした。")
        print("[ステッカー] ヒント: ウェブページのHTML構造を確認し、スクレイピング部分を調整してください。")
    
    print("=" * 50)
    print("[ステッカー] 処理が完了しました！")

if __name__ == "__main__":
    main()
