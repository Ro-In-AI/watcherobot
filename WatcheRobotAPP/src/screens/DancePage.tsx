import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';

// 舞蹈动作
interface DanceMove {
  id: string;
  name: string;
  duration: number; // 秒
}

// 预设舞蹈
const DANCES = [
  {
    id: 'dance1',
    name: '机器人舞',
    description: '经典的机器人风格动作',
    moves: [
      { id: 'd1-1', name: '举手', duration: 1 },
      { id: 'd1-2', name: '左右摆动', duration: 2 },
      { id: 'd1-3', name: '低头', duration: 1 },
      { id: 'd1-4', name: '举手', duration: 1 },
      { id: 'd1-5', name: '左右摆动', duration: 2 },
    ],
  },
  {
    id: 'dance2',
    name: 'wave舞',
    description: '流畅的波浪动作',
    moves: [
      { id: 'd2-1', name: '抬手', duration: 1 },
      { id: 'd2-2', name: 'wave', duration: 3 },
      { id: 'd2-3', name: '收手', duration: 1 },
    ],
  },
  {
    id: 'dance3',
    name: '功夫舞',
    description: '中国功夫风格的动作',
    moves: [
      { id: 'd3-1', name: '马步', duration: 2 },
      { id: 'd3-2', name: '出拳', duration: 1 },
      { id: 'd3-3', name: '收拳', duration: 1 },
      { id: 'd3-4', name: '出拳', duration: 1 },
      { id: 'd3-5', name: '收拳', duration: 1 },
    ],
  },
  {
    id: 'custom',
    name: '自定义舞蹈',
    description: '创建你自己的舞蹈',
    moves: [],
  },
];

export const DancePage: React.FC = () => {
  const [selectedDance, setSelectedDance] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentMove, setCurrentMove] = useState<number>(0);

  const handleDanceSelect = (danceId: string) => {
    setSelectedDance(danceId);
    setCurrentMove(0);
    // TODO: 加载舞蹈动作
    console.log('选择舞蹈:', danceId);
  };

  const handlePlay = () => {
    if (isPlaying) {
      setIsPlaying(false);
      // TODO: 停止播放
    } else {
      setIsPlaying(true);
      // TODO: 开始播放舞蹈
      console.log('开始播放舞蹈');
    }
  };

  const getTotalDuration = (moves: DanceMove[]) => {
    return moves.reduce((sum, move) => sum + move.duration, 0);
  };

  const selectedDanceData = DANCES.find((d) => d.id === selectedDance);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>舞蹈编排</Text>
        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>
            {isPlaying ? '播放中' : '就绪'}
          </Text>
        </View>
      </View>

      <ScrollView style={styles.content}>
        {/* 舞蹈列表 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>选择舞蹈</Text>
          {DANCES.map((dance) => (
            <TouchableOpacity
              key={dance.id}
              style={[
                styles.danceCard,
                selectedDance === dance.id && styles.danceCardActive,
              ]}
              onPress={() => handleDanceSelect(dance.id)}
            >
              <View style={styles.danceInfo}>
                <Text
                  style={[
                    styles.danceName,
                    selectedDance === dance.id && styles.danceNameActive,
                  ]}
                >
                  {dance.name}
                </Text>
                <Text style={styles.danceDesc}>{dance.description}</Text>
                {dance.moves.length > 0 && (
                  <Text style={styles.danceDuration}>
                    {dance.moves.length}个动作 · {getTotalDuration(dance.moves)}秒
                  </Text>
                )}
              </View>
              <View style={styles.danceArrow}>
                <Text style={styles.danceArrowText}>▶</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* 当前舞蹈详情 */}
        {selectedDanceData && selectedDanceData.moves.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>动作预览</Text>
            <View style={styles.movesContainer}>
              {selectedDanceData.moves.map((move, index) => (
                <View
                  key={move.id}
                  style={[
                    styles.moveItem,
                    currentMove === index && isPlaying && styles.moveItemActive,
                  ]}
                >
                  <View style={styles.moveNumber}>
                    <Text style={styles.moveNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.moveName}>{move.name}</Text>
                  <Text style={styles.moveDuration}>{move.duration}秒</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* 播放控制 */}
        <View style={styles.section}>
          <TouchableOpacity
            style={[
              styles.playButton,
              !selectedDance && styles.playButtonDisabled,
            ]}
            onPress={handlePlay}
            disabled={!selectedDance}
          >
            <Text style={styles.playButtonText}>
              {isPlaying ? '停止' : '播放舞蹈'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#F2F2F7',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#000',
  },
  statusBadge: {
    backgroundColor: '#FF9500',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '500',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    color: '#6E6E73',
    textTransform: 'uppercase',
    marginBottom: 12,
    marginLeft: 4,
  },
  danceCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  danceCardActive: {
    backgroundColor: '#007AFF',
  },
  danceInfo: {
    flex: 1,
  },
  danceName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  danceNameActive: {
    color: '#FFF',
  },
  danceDesc: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 2,
  },
  danceDuration: {
    fontSize: 12,
    color: '#8E8E93',
  },
  danceArrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  danceArrowText: {
    fontSize: 12,
    color: '#007AFF',
  },
  movesContainer: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    overflow: 'hidden',
  },
  moveItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  moveItemActive: {
    backgroundColor: '#007AFF20',
  },
  moveNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  moveNumberText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '600',
  },
  moveName: {
    flex: 1,
    fontSize: 14,
    color: '#000',
  },
  moveDuration: {
    fontSize: 12,
    color: '#8E8E93',
  },
  playButton: {
    backgroundColor: '#FF9500',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  playButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  playButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
