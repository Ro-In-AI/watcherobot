import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, View, StyleSheet } from 'react-native';

import {
  BluetoothPage,
  ControlPage,
  MotionPage,
  DancePage,
} from '../screens';

// 导航参数类型
export type RootTabParamList = {
  Bluetooth: undefined;
  Control: undefined;
  Motion: undefined;
  Dance: undefined;
};

const Tab = createBottomTabNavigator<RootTabParamList>();

// Tab 图标组件
const TabIcon: React.FC<{ name: string; focused: boolean; icon: string }> = ({
  name,
  focused,
  icon,
}) => (
  <View style={styles.tabIconContainer}>
    <Text style={[styles.tabIcon, focused && styles.tabIconFocused]}>
      {icon}
    </Text>
  </View>
);

export const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: styles.tabBar,
          tabBarActiveTintColor: '#007AFF',
          tabBarInactiveTintColor: '#8E8E93',
          tabBarLabelStyle: styles.tabBarLabel,
        }}
      >
        <Tab.Screen
          name="Bluetooth"
          component={BluetoothPage}
          options={{
            title: '蓝牙',
            tabBarIcon: ({ focused }) => (
              <TabIcon name="bluetooth" focused={focused} icon="📡" />
            ),
          }}
        />
        <Tab.Screen
          name="Control"
          component={ControlPage}
          options={{
            title: '控制',
            tabBarIcon: ({ focused }) => (
              <TabIcon name="control" focused={focused} icon="🎮" />
            ),
          }}
        />
        <Tab.Screen
          name="Motion"
          component={MotionPage}
          options={{
            title: '动作',
            tabBarIcon: ({ focused }) => (
              <TabIcon name="motion" focused={focused} icon="🤖" />
            ),
          }}
        />
        <Tab.Screen
          name="Dance"
          component={DancePage}
          options={{
            title: '舞蹈',
            tabBarIcon: ({ focused }) => (
              <TabIcon name="dance" focused={focused} icon="💃" />
            ),
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#FFF',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E5E5EA',
    paddingTop: 8,
    paddingBottom: 8,
    height: 60,
  },
  tabBarLabel: {
    fontSize: 11,
    fontWeight: '500',
  },
  tabIconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabIcon: {
    fontSize: 22,
    opacity: 0.6,
  },
  tabIconFocused: {
    opacity: 1,
  },
});
