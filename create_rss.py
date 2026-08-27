import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import time
import os

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
    
    print("📡 ウェブページにアクセス中...")
    
    try:
        # ページを取得
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()  # エラーがあれば例外を発生
        response.encoding = 'utf-8'  # 文字コードを指定
        
        print("✅ ページ取得成功！")
        
    except Exception as e:
        print(f"❌ ページ取得エラー: {e}")
        return []
    
    # BeautifulSoupで解析
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # ニュースレター一覧を格納するリスト
    articles = []
    
    # 記事の要素を探す（実際のHTML構造に合わせて調整が必要）
    # ここでは例として、通常のニュース一覧の構造を想定
    # 実際のページ構造を確認してセレクタを調整してください
    
    # 方法1: テーブル形式の場合
    # table_rows = soup.select('table tr')
    
    # 方法2: divリスト形式の場合
    article_items = soup.find_all('div', class_='news-item')  # クラス名は仮定
    
    # もし上記で見つからない場合は、すべてのリンクから探す
    if not article_items:
        # タイトルに「中国最新法律News」を含むリンクを探す
        all_links = soup.find_all('a')
        for link in all_links:
            title = link.get_text(strip=True)
            if '中国最新法律News' in title:
                href = link.get('href')
                if href:
                    # 絶対URLに変換
                    if href.startswith('/'):
                        href = 'https://www.ohebashi.com' + href
                    elif not href.startswith('http'):
                        href = 'https://www.ohebashi.com/jp/newsletter/' + href
                    
                    # 日付情報を探す（親要素や周辺要素から）
                    parent = link.find_parent()
                    date_text = ""
                    if parent:
                        # 日付っぽいテキストを探す（例: 2024年1月1日）
                        parent_text = parent.get_text()
                        # 簡単な日付抽出（実際はもっと精密に）
                        import re
                        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', parent_text)
                        if date_match:
                            date_text = f"{date_match.group(1)}-{date_match.group(2):0>2}-{date_match.group(3):0>2}"
                    
                    articles.append({
                        'title': title,
                        'link': href,
                        'date': date_text,
                        'description': f"大江橋法律事務所 中国最新法律News: {title}"
                    })
    
    print(f"📝 {len(articles)}件の記事が見つかりました")
    
    # 日付でソート（新しい順）
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    return articles

def generate_rss(articles):
    """RSSフィードを生成"""
    
    if not articles:
        print("⚠️ 記事が見つからないため、RSSを生成しません")
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
        
        # 日付があれば設定
        if article['date']:
            try:
                # 日付文字列をパース
                pub_date = datetime.strptime(article['date'], '%Y-%m-%d')
                fe.pubDate(pub_date.strftime('%a, %d %b %Y %H:%M:%S +0900'))
            except:
                # パースできない場合は現在時刻
                fe.pubDate(datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900'))
        else:
            fe.pubDate(datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900'))
        
        # GUID（一意識別子）
        fe.guid(article['link'], permalink=True)
    
    # RSSファイルを保存
    rss_path = 'rss.xml'
    fg.rss_file(rss_path)
    print(f"✅ RSSフィードを生成しました: {rss_path}")
    
    # ファイルサイズを表示
    file_size = os.path.getsize(rss_path)
    print(f"📊 ファイルサイズ: {file_size} bytes")

def main():
    """メイン関数"""
    print("🚀 RSSフィード生成を開始します...")
    print("=" * 50)
    
    # スクレイピング実行
    articles = scrape_newsletter()
    
    # RSS生成
    if articles:
        generate_rss(articles)
    else:
        print("⚠️ 記事が見つかりませんでした。")
        print("💡 ヒント: ウェブページのHTML構造を確認し、スクレイピング部分を調整してください。")
    
    print("=" * 50)
    print("🏁 処理が完了しました！")

if __name__ == "__main__":
    main()